# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

import os
import re
import sys
import time
from argparse import ArgumentParser
from urlparse import urlparse
from collections import defaultdict
from datetime import datetime, timedelta
from operator import itemgetter, attrgetter
from itertools import ifilter

import pytz
from babel import dates
from flask import Flask
from flask_migrate import stamp
from sqlalchemy.sql import func, select
from ZODB import DB, FileStorage
from ZODB.broken import find_global, Broken
from ZEO.ClientStorage import ClientStorage

from indico.core.db.sqlalchemy import db
from indico.core.db.sqlalchemy.migration import migrate as alembic_migrate
from indico.core.db.sqlalchemy.util import delete_all_tables, update_session_options
from indico.modules.rb import settings as rb_settings
from indico.modules.rb.models.aspects import Aspect
from indico.modules.rb.models.blocked_rooms import BlockedRoom
from indico.modules.rb.models.blocking_principals import BlockingPrincipal
from indico.modules.rb.models.blockings import Blocking
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.photos import Photo
from indico.modules.rb.models.reservation_edit_logs import ReservationEditLog
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import RepeatMapping, Reservation
from indico.modules.rb.models.room_attributes import RoomAttributeAssociation, RoomAttribute
from indico.modules.rb.models.room_bookable_hours import BookableHours
from indico.modules.rb.models.equipment import EquipmentType
from indico.modules.rb.models.room_nonbookable_periods import NonBookablePeriod
from indico.modules.rb.models.rooms import Room
from indico.util.console import colored, cformat, verbose_iterator
from indico.util.date_time import as_utc
from indico.util.string import is_valid_mail, safe_upper
from indico.web.flask.app import fix_root_path


month_names = [(str(i), name[:3].encode('utf-8').lower())
               for i, name in dates.get_month_names(locale='fr_FR').iteritems()]

attribute_map = {
    'Simba List': 'Manager Group',
    'Booking Simba List': 'Allowed Booking Group'
}


class NotBroken(Broken):
    """Like Broken, but it makes the attributes available"""
    def __setstate__(self, state):
        self.__dict__.update(state)


class UnbreakingDB(DB):
    def classFactory(self, connection, modulename, globalname):
        return find_global(modulename, globalname, Broken=NotBroken)


def get_storage(zodb_uri):
    uri_parts = urlparse(zodb_uri)

    print colored("Trying to open {}...".format(zodb_uri), 'green')

    if uri_parts.scheme == 'zeo':
        if uri_parts.port is None:
            print colored("No ZEO port specified. Assuming 9675", 'yellow')

        storage = ClientStorage((uri_parts.hostname, uri_parts.port or 9675),
                                username=uri_parts.username,
                                password=uri_parts.password,
                                realm=uri_parts.path[1:])

    elif uri_parts.scheme in ('file', None):
        storage = FileStorage.FileStorage(uri_parts.path)
    else:
        raise Exception("URI scheme not known: %s")
    print colored("Done!", 'green')
    return storage


def setup(main_zodb_uri, rb_zodb_uri, sqlalchemy_uri):
    app = Flask('migration')
    fix_root_path(app)
    app.config['SQLALCHEMY_DATABASE_URI'] = sqlalchemy_uri
    db.init_app(app)
    alembic_migrate.init_app(app, db, os.path.join(app.root_path, '..', 'migrations'))

    main_root = UnbreakingDB(get_storage(main_zodb_uri)).open().root()
    rb_root = UnbreakingDB(get_storage(rb_zodb_uri)).open().root()

    return main_root, rb_root, app


def convert_reservation_repeatability(old):
    return RepeatMapping.getNewMapping(old)


def generate_name(old_room):
    return '{}-{}-{}'.format(
        old_room.building,
        old_room.floor,
        old_room.roomNr
    )


def get_canonical_name_of(old_room):
    return '{}-{}'.format(
        old_room._locationName,
        generate_name(old_room)
    )


def get_room_id(guid):
    """ location | room_id """
    return int(guid.split('|')[1].strip())


def parse_dt_string(value):
    try:
        return datetime.strptime(value, '%d %b %Y %H:%M')
    except ValueError:
        # French month name
        for num, name in month_names:
            if name in value:
                value = value.lower().replace(name, num)
                break
        return datetime.strptime(value, '%d %m %Y %H:%M')


def convert_to_unicode(val):
    if isinstance(val, str):
        try:
            return unicode(val, 'utf-8')
        except UnicodeError:
            return unicode(val, 'latin1')
    elif isinstance(val, unicode):
        return val
    elif isinstance(val, int):
        return unicode(val)
    elif val is None:
        return u''
    raise RuntimeError('Unexpected type is found for unicode conversion')


def utc_to_local(dt):
    assert dt.tzinfo is None
    return dt - timedelta(seconds=time.altzone)


def migrate_settings(main_root):
    print cformat('%{white!}migrating settings')
    rb_settings.delete_all()
    opts = main_root['plugins']['RoomBooking']._PluginBase__options

    # Admins & authorized users/groups
    for old_key, new_key in (('AuthorisedUsersGroups', 'authorized_principals'),
                             ('Managers', 'admin_principals')):
        principals = set()
        for principal in opts[old_key].getValue():
            if principal.__class__.__name__ == 'Avatar':
                principals.add(('Avatar', principal.id))
            else:
                principals.add(('Group', principal.id))
        rb_settings.set(new_key, list(principals))
    # Assistance emails
    emails = [email for email in opts['assistanceNotificationEmails'].getValue() if is_valid_mail(email, False)]
    rb_settings.set('assistance_emails', emails)
    # Simple settings
    rb_settings.set('notification_hour', opts['notificationHour'].getValue())
    rb_settings.set('notification_before_days', opts['notificationBefore'].getValue())
    db.session.commit()


def migrate_locations(main_root, rb_root):
    print cformat('%{white!}migrating locations')
    default_location_name = main_root['DefaultRoomBookingLocation']
    custom_attributes_dict = rb_root['CustomAttributesList']

    for old_location in main_root['RoomBookingLocationList']:
        # create location
        l = Location(
            name=convert_to_unicode(old_location.friendlyName),
            is_default=(old_location.friendlyName == default_location_name)
        )

        print cformat('- %{cyan}{}').format(l.name)

        # add aspects
        for old_aspect in old_location._aspects.values():
            a = Aspect(
                name=convert_to_unicode(old_aspect.name),
                center_latitude=old_aspect.centerLatitude,
                center_longitude=old_aspect.centerLongitude,
                zoom_level=old_aspect.zoomLevel,
                top_left_latitude=old_aspect.topLeftLatitude,
                top_left_longitude=old_aspect.topLeftLongitude,
                bottom_right_latitude=old_aspect.bottomRightLatitude,
                bottom_right_longitude=old_aspect.bottomRightLongitude
            )

            print cformat('  %{blue!}Aspect:%{reset} {}').format(a.name)

            l.aspects.append(a)
            if old_aspect.defaultOnStartup:
                l.default_aspect = a

        # add custom attributes
        for ca in custom_attributes_dict.get(l.name, []):
            if ca['type'] != 'str':
                raise RuntimeError('Non-str custom attributes are unsupported: {}'.format(ca))
            attr_name = attribute_map.get(ca['name'], ca['name'])
            attr = RoomAttribute(name=attr_name.replace(' ', '-').lower(), title=attr_name, type=ca['type'],
                                 is_required=ca['required'], is_hidden=ca['hidden'])
            l.attributes.append(attr)
            print cformat('  %{blue!}Attribute:%{reset} {}').format(attr.title)

        # add new created location
        db.session.add(l)
        print
        print
    db.session.commit()


def migrate_rooms(rb_root, photo_path, avatar_id_map):
    eq = defaultdict(set)
    vc = defaultdict(set)
    for old_room_id, old_room in rb_root['Rooms'].iteritems():
        eq[old_room._locationName].update(e for e in old_room._equipment.split('`') if e)
        vc[old_room._locationName].update(e for e in getattr(old_room, 'avaibleVC', []) if e)

    print cformat('%{white!}migrating equipment')
    for name, eqs in eq.iteritems():
        l = Location.find_first(name=name)
        l.equipment_types.extend(EquipmentType(name=x) for x in eqs)
        print cformat('- [%{cyan}{}%{reset}] {}').format(name, eqs)
        db.session.add(l)
    db.session.commit()
    print

    print cformat('%{white!}migrating vc equipment')
    for name, vcs in vc.iteritems():
        l = Location.find_first(name=name)
        pvc = l.get_equipment_by_name('Video conference')
        for vc_name in vcs:
            req = EquipmentType(name=vc_name)
            req.parent = pvc
            l.equipment_types.append(req)
            print cformat('- [%{cyan}{}%{reset}] {}').format(name, req.name)
        db.session.add(l)
    db.session.commit()
    print

    print cformat('%{white!}migrating rooms')
    for old_room_id, old_room in rb_root['Rooms'].iteritems():
        l = Location.find_first(name=old_room._locationName)
        r = Room(
            id=old_room_id,
            name=convert_to_unicode((old_room._name or '').strip() or generate_name(old_room)),
            site=convert_to_unicode(old_room.site),
            division=convert_to_unicode(old_room.division),
            building=convert_to_unicode(old_room.building),
            floor=convert_to_unicode(old_room.floor),
            number=convert_to_unicode(old_room.roomNr),

            notification_before_days=((old_room.resvStartNotificationBefore or None)
                                      if getattr(old_room, 'resvStartNotification', False)
                                      else None),
            notification_for_responsible=getattr(old_room, 'resvNotificationToResponsible', False),
            notification_for_assistance=getattr(old_room, 'resvNotificationAssistance', False),

            reservations_need_confirmation=old_room.resvsNeedConfirmation,

            telephone=old_room.telephone,
            key_location=convert_to_unicode(old_room.whereIsKey),

            capacity=old_room.capacity,
            surface_area=getattr(old_room, 'surfaceArea', None),
            latitude=getattr(old_room, 'latitude', None),
            longitude=getattr(old_room, 'longitude', None),

            comments=convert_to_unicode(old_room.comments),

            owner_id=avatar_id_map.get(old_room.responsibleId, old_room.responsibleId),

            is_active=old_room.isActive,
            is_reservable=old_room.isReservable,
            max_advance_days=int(old_room.maxAdvanceDays) if getattr(old_room, 'maxAdvanceDays', None) else None
        )

        print cformat('- [%{cyan}{}%{reset}] %{grey!}{:4}%{reset}  %{green!}{}%{reset}').format(l.name, r.id, r.name)

        for old_bookable_time in getattr(old_room, '_dailyBookablePeriods', []):
            r.bookable_hours.append(
                BookableHours(
                    start_time=old_bookable_time._startTime,
                    end_time=old_bookable_time._endTime
                )
            )
            print cformat('  %{blue!}Bookable:%{reset} {}').format(r.bookable_hours[-1])

        for old_nonbookable_date in getattr(old_room, '_nonBookableDates', []):
            r.nonbookable_periods.append(
                NonBookablePeriod(
                    start_dt=old_nonbookable_date._startDate,
                    end_dt=old_nonbookable_date._endDate
                )
            )
            print cformat('  %{blue!}Nonbookable:%{reset} {}').format(r.nonbookable_periods[-1])

        if photo_path:
            try:
                with open(os.path.join(photo_path, 'large_photos',
                          get_canonical_name_of(old_room) + '.jpg'), 'rb') as f:
                    large_photo = f.read()
            except Exception:
                large_photo = None

            try:
                with open(os.path.join(photo_path, 'small_photos',
                          get_canonical_name_of(old_room) + '.jpg'), 'rb') as f:
                    small_photo = f.read()
            except Exception:
                small_photo = None

            if large_photo and small_photo:
                r.photo = Photo(data=large_photo, thumbnail=small_photo)
                print cformat('  %{blue!}Photos')

        new_eq = []
        for old_equipment in ifilter(None, old_room._equipment.split('`') + old_room.avaibleVC):
            room_eq = l.get_equipment_by_name(old_equipment)
            new_eq.append(room_eq)
            r.available_equipment.append(room_eq)
        if new_eq:
            print cformat('  %{blue!}Equipment:%{reset} {}').format(', '.join(sorted(x.name for x in new_eq)))

        for attr_name, value in getattr(old_room, 'customAtts', {}).iteritems():
            value = convert_to_unicode(value)
            if not value or ('Simba' in attr_name and value == u'Error: unknown mailing list'):
                continue
            attr_name = attribute_map.get(attr_name, attr_name).replace(' ', '-').lower()
            ca = l.get_attribute_by_name(attr_name)
            if not ca:
                print cformat('  %{blue!}Attribute:%{reset} {} %{red!}not found').format(attr_name)
                continue
            attr = RoomAttributeAssociation()
            attr.value = value
            attr.attribute = ca
            r.attributes.append(attr)
            print cformat('  %{blue!}Attribute:%{reset} {} = {}').format(attr.attribute.title, attr.value)

        l.rooms.append(r)
        db.session.add(l)
        print
    db.session.commit()


def migrate_reservations(main_root, rb_root, avatar_id_map):
    print cformat('%{white!}migrating reservations')
    i = 1
    for rid, v in rb_root['Reservations'].iteritems():
        room = Room.get(v.room.id)
        if room is None:
            print cformat('  %{red!}skipping resv for dead room {0.room.id}: {0.id} ({0._utcCreatedDT})').format(v)
            continue

        repeat_frequency, repeat_interval = convert_reservation_repeatability(v.repeatability)
        booked_for_id = getattr(v, 'bookedForId', None)

        r = Reservation(
            id=v.id,
            created_dt=as_utc(v._utcCreatedDT),
            start_dt=utc_to_local(v._utcStartDT),
            end_dt=utc_to_local(v._utcEndDT),
            booked_for_id=avatar_id_map.get(booked_for_id, booked_for_id) or None,
            booked_for_name=convert_to_unicode(v.bookedForName),
            contact_email=convert_to_unicode(v.contactEmail),
            contact_phone=convert_to_unicode(getattr(v, 'contactPhone', None)),
            created_by_id=avatar_id_map.get(v.createdBy, v.createdBy) or None,
            is_cancelled=v.isCancelled,
            is_accepted=v.isConfirmed,
            is_rejected=v.isRejected,
            booking_reason=convert_to_unicode(v.reason),
            rejection_reason=convert_to_unicode(getattr(v, 'rejectionReason', None)),
            repeat_frequency=repeat_frequency,
            repeat_interval=repeat_interval,
            uses_vc=getattr(v, 'usesAVC', False),
            needs_vc_assistance=getattr(v, 'needsAVCSupport', False),
            needs_assistance=getattr(v, 'needsAssistance', False)
        )

        for eq_name in getattr(v, 'useVC', []):
            eq = room.location.get_equipment_by_name(eq_name)
            if eq:
                r.used_equipment.append(eq)

        occurrence_rejection_reasons = {}
        if getattr(v, 'resvHistory', None):
            for h in reversed(v.resvHistory._entries):
                ts = as_utc(parse_dt_string(h._timestamp))

                if len(h._info) == 2:
                    possible_rejection_date, possible_rejection_reason = h._info
                    m = re.match(r'Booking occurrence of the (\d{1,2} \w{3} \d{4}) rejected',
                                 possible_rejection_reason)
                    if m:
                        d = datetime.strptime(m.group(1), '%d %b %Y')
                        occurrence_rejection_reasons[d] = possible_rejection_reason[9:].strip('\'')

                el = ReservationEditLog(
                    timestamp=ts,
                    user_name=h._responsibleUser,
                    info=map(convert_to_unicode, h._info)
                )
                r.edit_logs.append(el)

        notifications = getattr(v, 'startEndNotification', []) or []
        excluded_days = getattr(v, '_excludedDays', []) or []
        ReservationOccurrence.create_series_for_reservation(r)
        for occ in r.occurrences:
            occ.notification_sent = occ.date in notifications
            occ.is_rejected = r.is_rejected
            occ.is_cancelled = r.is_cancelled or occ.date in excluded_days
            occ.rejection_reason = (convert_to_unicode(occurrence_rejection_reasons[occ.date])
                                    if occ.date in occurrence_rejection_reasons else None)

        event_id = getattr(v, '_ReservationBase__owner', None)
        if hasattr(event_id, '_Impersistant__obj'):  # Impersistant object
            event_id = event_id._Impersistant__obj
        if event_id is not None:
            event = main_root['conferences'].get(event_id)
            if event:
                # For some stupid reason there are bookings in the database which have a completely unrelated parent
                # TODO: Maybe use a separate migration step which iterates over all events? Would be slower but safer!
                guids = getattr(event, '_Conference__roomBookingGuids', [])
                if any(int(x.id) == v.id for x in guids if x.id is not None):
                    r.event_id = int(event_id)
                else:
                    print cformat('  %{red}event {} does not contain booking {}').format(event_id, v.id)

        print cformat('- [%{cyan}{}%{reset}/%{green!}{}%{reset}]  %{grey!}{}%{reset}  {}').format(room.location_name,
                                                                                                  room.name,
                                                                                                  r.id,
                                                                                                  r.created_dt.date())

        room.reservations.append(r)
        db.session.add(room)
        i = (i + 1) % 1000
        if not i:
            db.session.commit()
    db.session.commit()


def migrate_blockings(rb_root, avatar_id_map):
    state_map = {
        None: BlockedRoom.State.pending,
        False: BlockedRoom.State.rejected,
        True: BlockedRoom.State.accepted
    }

    print cformat('%{white!}migrating blockings')
    for old_blocking_id, old_blocking in rb_root['RoomBlocking']['Blockings'].iteritems():
        b = Blocking(
            id=old_blocking.id,
            created_by_id=avatar_id_map.get(old_blocking._createdBy, old_blocking._createdBy),
            created_dt=as_utc(old_blocking._utcCreatedDT),
            start_date=old_blocking.startDate,
            end_date=old_blocking.endDate,
            reason=convert_to_unicode(old_blocking.message)
        )

        print cformat(u'- %{cyan}{}').format(b.reason)
        for old_blocked_room in old_blocking.blockedRooms:
            br = BlockedRoom(
                state=state_map[old_blocked_room.active],
                rejected_by=old_blocked_room.rejectedBy,
                rejection_reason=convert_to_unicode(old_blocked_room.rejectionReason),
            )
            room = Room.get(get_room_id(old_blocked_room.roomGUID))
            room.blocked_rooms.append(br)
            b.blocked_rooms.append(br)
            print cformat(u'  %{blue!}Room:%{reset} {} ({})').format(room.full_name,
                                                                     BlockedRoom.State(br.state).title)

        for old_principal in old_blocking.allowed:
            principal_id = old_principal._id
            if old_principal._type == 'Avatar':
                principal_id = avatar_id_map.get(old_principal._id, old_principal._id)
            bp = BlockingPrincipal(
                entity_type=old_principal._type,
                entity_id=principal_id
            )
            b.allowed.append(bp)
            print cformat(u'  %{blue!}Allowed:%{reset} {}({})').format(bp.entity_type, bp.entity_id)
        db.session.add(b)
    db.session.commit()


def fix_sequences():
    for name, cls in sorted(db.Model._decl_class_registry.iteritems(), key=itemgetter(0)):
        table = getattr(cls, '__table__', None)
        if table is None:
            continue
        # Check if we have a single autoincrementing primary key
        candidates = [col for col in table.c if col.autoincrement and col.primary_key]
        if len(candidates) != 1 or not isinstance(candidates[0].type, db.Integer):
            continue
        serial_col = candidates[0]
        sequence_name = '{}.{}_{}_seq'.format(table.schema, cls.__tablename__, serial_col.name)

        query = select([func.setval(sequence_name, func.max(serial_col) + 1)], table)
        db.session.execute(query)
    db.session.commit()


def find_merged_avatars(main_root):
    print cformat('%{white!}checking for merged avatars')
    avatar_id_map = {}
    for avatar in verbose_iterator(main_root['avatars'].itervalues(), len(main_root['avatars']), attrgetter('id'),
                                   lambda av: '{}, {}'.format(safe_upper(av.surName), av.name)):
        for merged_avatar in getattr(avatar, '_mergeFrom', []):
            avatar_id_map[merged_avatar.getId()] = avatar.getId()
    return avatar_id_map


def migrate(main_root, rb_root, photo_path, merged_avatars):
    avatar_id_map = find_merged_avatars(main_root) if merged_avatars else {}
    migrate_settings(main_root)
    migrate_locations(main_root, rb_root)
    migrate_rooms(rb_root, photo_path, avatar_id_map)
    migrate_blockings(rb_root, avatar_id_map)
    migrate_reservations(main_root, rb_root, avatar_id_map)
    fix_sequences()


def main(main_uri, rb_uri, sqla_uri, photo_path, drop, merged_avatars):
    update_session_options(db)  # get rid of the zope transaction extension
    main_root, rb_root, app = setup(main_uri, rb_uri, sqla_uri)
    global tz
    try:
        tz = pytz.timezone(main_root['MaKaCInfo']['main'].getTimezone())
    except KeyError:
        tz = pytz.utc

    start = time.clock()
    with app.app_context():
        if drop:
            print cformat('%{yellow!}*** DANGER')
            print cformat('%{yellow!}***%{reset} '
                          '%{red!}ALL DATA%{reset} in your database %{yellow!}{!r}%{reset} will be '
                          '%{red!}PERMANENTLY ERASED%{reset}!').format(db.engine.url)
            if raw_input(cformat('%{yellow!}***%{reset} To confirm this, enter %{yellow!}YES%{reset}: ')) != 'YES':
                print 'Aborting'
                sys.exit(1)
            delete_all_tables(db)
        stamp()
        db.create_all()
        if Location.find().count():
            # Usually there's no good reason to migrate with data in the DB. However, during development one might
            # comment out some migration tasks and run the migration anyway.
            print cformat('%{yellow!}*** WARNING')
            print cformat('%{yellow!}***%{reset} Your database is not empty, migration will most likely fail!')
            if raw_input(cformat('%{yellow!}***%{reset} To confirm this, enter %{yellow!}YES%{reset}: ')) != 'YES':
                print 'Aborting'
                sys.exit(1)
        migrate(main_root, rb_root, photo_path, merged_avatars)
    print 'migration took {} seconds'.format((time.clock() - start))


if __name__ == '__main__':
    parser = ArgumentParser(prog='migration')
    parser.add_argument('main', help='main ZODB storage URI (zeo:// or file://)', metavar="MAIN_ZODB_URI")
    parser.add_argument('rb', help='Room Booking ZODB file storage URI (zeo:// or file://)', metavar="RB_ZODB_URI")
    parser.add_argument('uri', help='SQLAlchemy database uri', metavar="SQLALCHEMY_URI")
    parser.add_argument('-d', '--drop', help='drop any existing database', action='store_true')
    parser.add_argument('-m', '--merged', help='take merged avatars into account', action='store_true')
    parser.add_argument('-p', '--photo', help='path to photos of rooms')

    args = parser.parse_args()
    main(args.main, args.rb, args.uri, args.photo, args.drop, args.merged)
