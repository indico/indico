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

__no_session_options__ = True

import os
import re
from argparse import ArgumentParser
from urlparse import urlparse
from collections import defaultdict
from datetime import datetime, time as dt_time, timedelta
from itertools import ifilter
from time import clock

import pytz
from babel import dates
from flask import Flask
from ZODB import DB, FileStorage
from ZEO.ClientStorage import ClientStorage

from indico.core.db import db, drop_database
from indico.core.db.migration import MigratedDB
from indico.modules.rb.models import *
from indico.util.console import colored, cformat

month_names = [(str(i), name[:3].encode('utf-8').lower())
               for i, name in dates.get_month_names(locale='fr_FR').iteritems()]


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
    app.config['SQLALCHEMY_DATABASE_URI'] = sqlalchemy_uri
    db.init_app(app)

    main_root = MigratedDB(get_storage(main_zodb_uri)).open().root()
    rb_root = DB(get_storage(rb_zodb_uri)).open().root()

    return main_root, rb_root, app


def teardown():
    pass


def convert_reservation_repeatibility(old):
    return RepeatMapping.getNewMapping(old)


def convert_room_notification_for_start(flag, before):
    return before if flag else 0


def convert_room_max_advance_days(old):
    return int(old) if old else 30


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


def convert_date(ds):
    if isinstance(ds, str):
        try:
            ds = datetime.strptime(ds, '%d %b %Y %H:%M')
        except ValueError:

            for i, n in month_names:
                if n in ds:
                    ds = ds.lower().replace(n, i)
                    break
            try:
                ds = datetime.strptime(ds, '%d %m %Y %H:%M')
            except:
                raise RuntimeError(ds)
    if isinstance(ds, datetime):
        if not ds.tzinfo:
            ds = tz.localize(ds)
    elif isinstance(ds, dt_time):
        hour_diff = datetime.now(pytz.utc).hour - datetime.now(tz).hour
        ds = ds.replace(hour=(ds.hour+hour_diff) % 24)  # day light save time?
    return ds


def convert_to_unicode(val):
    if isinstance(val, str):
        try:
            return unicode(val, 'utf-8')
        except:
            return unicode(val, 'latin1')
    elif isinstance(val, unicode):
        return val
    elif isinstance(val, int):
        return unicode(val)
    elif val is None:
        return u''
    raise RuntimeError('Unexpected type is found for unicode conversion')


def merge_custom_attributes(attrs):
    res = defaultdict(dict)
    for attr in attrs:
        if isinstance(attr, str):
            name = convert_to_unicode(attr)
            value = {}
        elif isinstance(old_custom_attribute, dict):
            if 'name' in attr:
                name = convert_to_unicode(attr.pop('name'))
            else:
                name = 'unknown'
            value = attr
        else:
            raise RuntimeError('Unexpected custom attribute type')

        res[name.lower()].update(value)
    return res


def migrate_locations(main_root, rb_root):
    print cformat('%{white!}migrating locations')
    default_location_name = main_root['DefaultRoomBookingLocation']
    custom_attributes_dict = rb_root['CustomAttributesList']

    for old_location in main_root['RoomBookingLocationList']:
        # create location
        l = Location(
            name=convert_to_unicode(old_location.friendlyName),
            support_emails=convert_to_unicode(','.join(old_location._avcSupportEmails)),
            is_default=(old_location.friendlyName == default_location_name)
        )

        print cformat('- %{cyan}{}').format(l.name)

        # add aspects
        for old_aspect in old_location.aspects.values():
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
            l.addAttribute(ca['name'].lower(), {
                'is_required': ca['required'],
                'is_hidden': ca['hidden'],
                'type': 'str'
            })
            print cformat('  %{blue!}Attribute:%{reset} {}').format(l.attributes[-1].name)

        # add new created location
        db.session.add(l)
        print
        print
    db.session.commit()


def migrate_rooms(rb_root, photo_path):
    eq = defaultdict(set)
    vc = defaultdict(set)
    for old_room_id, old_room in rb_root['Rooms'].iteritems():
        eq[old_room._locationName].update(e.lower() for e in old_room._equipment.split('`') if e)
        vc[old_room._locationName].update(e.lower() for e in getattr(old_room, 'avaibleVC', []) if e)

    print cformat('%{white!}migrating equipment')
    for name, eqs in eq.iteritems():
        l = Location.getLocationByName(name)
        l.equipments.extend(eqs)
        print cformat('- [%{cyan}{}%{reset}] {}').format(name, eqs)
        db.session.add(l)
    db.session.commit()
    print

    print cformat('%{white!}migrating vc equipment')
    for name, vcs in vc.iteritems():
        l = Location.getLocationByName(name)
        pvc = l.getEquipmentByName('video conference')
        for vc_name in vcs:
            re = RoomEquipment(name=vc_name)
            re.parent = pvc
            l.equipment_objects.append(re)
            print cformat('- [%{cyan}{}%{reset}] {}').format(name, re.name)
        db.session.add(l)
    db.session.commit()
    print

    print cformat('%{white!}migrating rooms')
    for old_room_id, old_room in rb_root['Rooms'].iteritems():
        l = Location.getLocationByName(old_room._locationName)
        r = Room(
            id=old_room_id,
            name=convert_to_unicode(old_room._name or generate_name(old_room)),
            site=convert_to_unicode(old_room.site),
            division=convert_to_unicode(old_room.site),
            building=convert_to_unicode(old_room.building),
            floor=convert_to_unicode(old_room.floor),
            number=convert_to_unicode(old_room.roomNr),

            notification_for_start=convert_room_notification_for_start(
                old_room.resvStartNotification,
                old_room.resvStartNotificationBefore
            ),
            notification_for_end=old_room.resvEndNotification,
            notification_for_responsible=old_room.resvNotificationToResponsible,
            notification_for_assistance=old_room.resvNotificationAssistance,

            reservations_need_confirmation=old_room.resvsNeedConfirmation,

            telephone=old_room.telephone,
            key_location=convert_to_unicode(old_room.whereIsKey),

            capacity=old_room.capacity,
            surface_area=old_room.surfaceArea,
            latitude=old_room.latitude,
            longitude=old_room.longitude,

            comments=convert_to_unicode(old_room.comments),

            owner_id=old_room.responsibleId,

            is_active=old_room.isActive,
            is_reservable=old_room.isReservable,
            max_advance_days=convert_room_max_advance_days(old_room.maxAdvanceDays)
        )

        print cformat('- [%{cyan}{}%{reset}] %{grey!}{:4}%{reset}  %{green!}{}%{reset}').format(l.name, r.id, r.name)

        for old_bookable_time in old_room.getDailyBookablePeriods():
            r.bookable_times.append(
                BookableTime(
                    start_time=convert_date(old_bookable_time._startTime),
                    end_time=convert_date(old_bookable_time._endTime)
                )
            )
            print cformat('  %{blue!}Bookable:%{reset} {}').format(r.bookable_times[-1])

        for old_nonbookable_date in old_room.getNonBookableDates():
            r.nonbookable_dates.append(
                NonBookableDate(
                    start_date=convert_date(old_nonbookable_date._startDate),
                    end_date=convert_date(old_nonbookable_date._endDate)
                )
            )
            print cformat('  %{blue!}Nonbookable:%{reset} {}').format(r.nonbookable_dates[-1])

        if photo_path:
            try:
                with open(os.path.join(photo_path, 'large_photos',
                          get_canonical_name_of(old_room) + '.jpg'), 'rb') as f:
                    large_photo = f.read()
            except:
                large_photo = None

            try:
                with open(os.path.join(photo_path, 'small_photos',
                          get_canonical_name_of(old_room) + '.jpg'), 'rb') as f:
                    small_photo = f.read()
            except:
                small_photo = None

            if large_photo and small_photo:
                r.photos.append(
                    Photo(
                        large_content=large_photo,
                        small_content=small_photo
                    )
                )
                print cformat('  %{blue!}Photos')

        new_eq = []
        for old_equipment in ifilter(None, (e.lower() for e in old_room._equipment.split('`'))):
            room_eq = l.getEquipmentByName(old_equipment)
            new_eq.append(room_eq)
            r.equipments.append(room_eq)
        if new_eq:
            print cformat('  %{blue!}Equipment:%{reset} {}').format(', '.join(sorted(x.name for x in new_eq)))

        for name, value in merge_custom_attributes(getattr(old_room, 'customAtts', [])).iteritems():
            ca = l.getAttributeByName(name)
            if ca:
                attr = RoomAttributeAssociation()
                attr.value = value
                attr.attribute = ca
                r.attributes.append(attr)
                print cformat('  %{blue!}Attribute:%{reset} {} = {}').format(attr.attribute, attr.value)
            else:
                print name, value, old_room.id, l.id  # these are already deleted from location

        l.rooms.append(r)
        db.session.add(l)
        print
    db.session.commit()


def migrate_reservations(rb_root):
    print cformat('%{white!}migrating reservations')
    i = 1
    for rid, v in rb_root['Reservations'].iteritems():
        l = Location.getLocationByName(v.locationName)
        room = Room.getRoomById(v.room.id)
        if room is None:
            print cformat('  %{red!}skipping resv for dead room {0.room.id}: {0.id} ({0._utcCreatedDT})').format(v)
            continue

        repeat_unit, repeat_step = convert_reservation_repeatibility(v.repeatability)

        r = Reservation(
            id=v.id,
            created_at=convert_date(v._utcCreatedDT),
            start_date=convert_date(v._utcStartDT),
            end_date=convert_date(v._utcEndDT),
            booked_for_id=convert_to_unicode(v.bookedForId or u'1073'),
            booked_for_name=convert_to_unicode(v.bookedForName),
            contact_email=convert_to_unicode(v.contactEmail),
            contact_phone=convert_to_unicode(v.contactPhone),
            created_by=convert_to_unicode(v.createdBy or u'1073'),
            is_cancelled=v.isCancelled,
            is_confirmed=v.isConfirmed,
            is_rejected=v.isRejected,
            booking_reason=convert_to_unicode(v.reason),
            rejection_reason=convert_to_unicode(v.rejectionReason),
            repeat_unit=repeat_unit,
            repeat_step=repeat_step,
            uses_video_conference=v.usesAVC,
            needs_video_conference_setup=v.needsAVCSupport,
            needs_general_assistance=v.needsAssistance
        )

        for eq_name in getattr(v, 'useVC', []):
            eq = l.getEquipmentByName(eq_name.lower())
            if eq:
                r.equipments.append(eq)

        occurrence_rejection_reasons = {}
        if getattr(v, 'resvHistory', None):
            entries = set()
            for h in reversed(v.resvHistory._entries):
                ts = convert_date(h._timestamp)
                while ts in entries:
                    ts += timedelta(milliseconds=1)
                entries.add(ts)

                if len(h._info) == 2:
                    possible_rejection_date, possible_rejection_reason = h._info
                    m = re.match(r'Booking occurrence of the (\d{1,2} \w{3} \d{4}) rejected',
                                 possible_rejection_reason)
                    if m:
                        d = datetime.strptime(m.group(1), '%d %b %Y')
                        occurrence_rejection_reasons[d] = possible_rejection_reason[9:].strip('\'')

                el = ReservationEditLog(
                    timestamp=ts,
                    avatar_id=h._responsibleUser,
                    info=convert_to_unicode('```'.join(h._info))
                )
                r.edit_logs.append(el)

        notifications = getattr(v, 'startEndNotification', []) or []
        excluded_days = getattr(v, '_excludedDays', []) or []
        for period in v.splitToPeriods():
            d = period.startDT.date()
            occ = ReservationOccurrence(
                start=convert_date(period.startDT),
                end=convert_date(period.endDT),
                is_sent=(d in notifications),
                is_cancelled=(d in excluded_days),
                rejection_reason=(convert_to_unicode(occurrence_rejection_reasons[d])
                                  if d in occurrence_rejection_reasons else None)
            )
            r.occurrences.append(occ)

        print cformat('- [%{cyan}{}%{reset}/%{green!}{}%{reset}]  %{grey!}{}%{reset}  {}').format(l.name, room.name,
                                                                                                  r.id,
                                                                                                  r.created_at.date())

        room.reservations.append(r)
        db.session.add(room)
        i = (i + 1) % 1000
        if not i:
            db.session.commit()
    db.session.commit()


def migrate_blockings(rb_root):

    for old_blocking_id, old_blocking in rb_root['RoomBlocking']['Blockings'].iteritems():
        b = Blocking(
            id=old_blocking.id,
            created_by=convert_to_unicode(old_blocking._createdBy),
            created_at=convert_date(old_blocking._utcCreatedDT),
            start_date=convert_date(datetime.combine(old_blocking.startDate, dt_time.min)),
            end_date=convert_date(datetime.combine(old_blocking.endDate, dt_time.max)),
            reason=convert_to_unicode(old_blocking.message)
        )

        for old_blocked_room in old_blocking.blockedRooms:
            br = BlockedRoom(
                is_active=old_blocked_room.active,
                notification_sent=old_blocked_room.notificationSent,
                rejected_by=old_blocked_room.rejectedBy,
                rejection_reason=convert_to_unicode(old_blocked_room.rejectionReason),
            )
            room = Room.getRoomById(get_room_id(old_blocked_room.roomGUID))
            room.blocked_rooms.append(br)
            b.blocked_rooms.append(br)

        for old_principal in old_blocking.allowed:
            bp = BlockingPrincipal(
                entity_type=old_principal._type,
                entity_id=old_principal._id
            )
            b.allowed.append(bp)
        db.session.add(b)
    db.session.commit()


def migrate(main_root, rb_root, photo_path):
    migrate_locations(main_root, rb_root)
    migrate_rooms(rb_root, photo_path)
    migrate_reservations(rb_root)
    migrate_blockings(rb_root)


def main(main_uri, rb_uri, sqla_uri, photo_path, drop):
    main_root, rb_root, app = setup(main_uri, rb_uri, sqla_uri)
    global tz
    try:
        tz = pytz.timezone(main_root['MaKaCInfo']['main'].getTimezone())
    except KeyError:
        tz = pytz.utc

    start = clock()
    with app.app_context():
        if drop:
            drop_database(db)
        db.create_all()
        migrate(main_root, rb_root, photo_path)
    print (clock() - start), 'seconds'


if __name__ == '__main__':
    parser = ArgumentParser(prog='migration')
    parser.add_argument('main', help='main ZODB storage URI (zeo:// or file://)', metavar="MAIN_ZODB_URI")
    parser.add_argument('rb', help='Room Booking ZODB file storage URI (zeo:// or file://)', metavar="RB_ZODB_URI")
    parser.add_argument('uri', help='SQLAlchemy database uri', metavar="SQLALCHEMY_URI")
    parser.add_argument('-d', '--drop', help='drop any existing database', action='store_true')
    parser.add_argument('-p', '--photo', help='path to photos of rooms')

    args = parser.parse_args()
    main(args.main, args.rb, args.uri, args.photo, args.drop)
