# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

# TODO: make --rb-zodb-uri optional and assume same DB in that case?
from collections import defaultdict
import os
import re

import time
from datetime import datetime, timedelta
from itertools import ifilter
from operator import attrgetter

import click
from babel import dates

from indico.core.db.sqlalchemy import db
from indico.modules.rb import rb_settings
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
from indico.util.console import cformat, verbose_iterator
from indico.util.date_time import as_utc
from indico.util.string import safe_upper, is_valid_mail
from indico_zodbimport import Importer, convert_to_unicode, convert_principal_list
from indico_zodbimport.util import UnbreakingDB, get_storage


french_month_names = [(str(i), name[:3].encode('utf-8').lower())
                      for i, name in dates.get_month_names(locale='fr_FR').iteritems()]

attribute_map = {
    'Simba List': 'Manager Group',
    'Booking Simba List': 'Allowed Booking Group'
}


def generate_name(old_room):
    return '{}-{}-{}'.format(old_room.building, old_room.floor, old_room.roomNr)


def get_canonical_name_of(old_room):
    return '{}-{}'.format(old_room._locationName, generate_name(old_room))


def get_room_id(guid):
    return int(guid.split('|')[1].strip())


def parse_dt_string(value):
    try:
        return datetime.strptime(value, '%d %b %Y %H:%M')
    except ValueError:
        # French month name
        for num, name in french_month_names:
            if name in value:
                value = value.lower().replace(name, num)
                break
        return datetime.strptime(value, '%d %m %Y %H:%M')


def utc_to_local(dt):
    assert dt.tzinfo is None
    return dt - timedelta(seconds=time.altzone)


# noinspection PyArgumentList
class RoomBookingImporter(Importer):
    def __init__(self, **kwargs):
        self.rb_zodb_uri = kwargs.pop('rb_zodb_uri')
        self.no_merged_avatars = kwargs.pop('no_merged_avatars')
        self.photo_path = kwargs.pop('photo_path')
        self.rb_root = None
        self.merged_avatars = {}
        super(RoomBookingImporter, self).__init__(**kwargs)

    @staticmethod
    def decorate_command(command):
        command = click.option('--rb-zodb-uri', required=True, help="ZODB URI for the room booking database")(command)
        command = click.option('--photo-path', type=click.Path(exists=True, file_okay=False),
                               help="path to the folder containing room photos")(command)
        command = click.option('--no-merged-avatars', default=False, is_flag=True,
                               help="speed up migration by not checking for merged avatars")(command)
        return command

    def connect_zodb(self):
        super(RoomBookingImporter, self).connect_zodb()
        self.rb_root = UnbreakingDB(get_storage(self.rb_zodb_uri)).open().root()

    def has_data(self):
        return Location.query.has_rows()

    def migrate(self):
        if not self.no_merged_avatars:
            self.find_merged_avatars()
        self.migrate_settings()
        self.migrate_locations()
        self.migrate_rooms()
        self.migrate_blockings()
        self.migrate_reservations()
        self.fix_sequences(schema='roombooking')

    def find_merged_avatars(self):
        print cformat('%{white!}checking for merged avatars')
        for avatar in verbose_iterator(self.zodb_root['avatars'].itervalues(), len(self.zodb_root['avatars']),
                                       attrgetter('id'), lambda av: '{}, {}'.format(safe_upper(av.surName), av.name)):
            for merged_avatar in getattr(avatar, '_mergeFrom', []):
                self.merged_avatars[merged_avatar.getId()] = avatar.getId()

    def migrate_settings(self):
        print cformat('%{white!}migrating settings')
        rb_settings.delete_all()
        opts = self.zodb_root['plugins']['RoomBooking']._PluginBase__options

        # Admins & authorized users/groups
        rb_settings.set('authorized_principals', convert_principal_list(opts['AuthorisedUsersGroups']))
        rb_settings.set('admin_principals', convert_principal_list(opts['Managers']))
        # Assistance emails
        emails = [email for email in opts['assistanceNotificationEmails']._PluginOption__value
                  if is_valid_mail(email, False)]
        rb_settings.set('assistance_emails', emails)
        # Simple settings
        rb_settings.set('notification_before_days', opts['notificationBefore']._PluginOption__value)
        db.session.commit()

    def migrate_locations(self):
        print cformat('%{white!}migrating locations')
        default_location_name = self.zodb_root['DefaultRoomBookingLocation']
        custom_attributes_dict = self.rb_root['CustomAttributesList']

        for old_location in self.zodb_root['RoomBookingLocationList']:
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

    def migrate_rooms(self):
        eq = defaultdict(set)
        vc = defaultdict(set)
        for old_room_id, old_room in self.rb_root['Rooms'].iteritems():
            eq[old_room._locationName].update(e for e in old_room._equipment.split('`') if e)
            vc[old_room._locationName].update(e for e in getattr(old_room, 'avaibleVC', []) if e)

        print cformat('%{white!}migrating equipment')
        for name, eqs in eq.iteritems():
            l = Location.find_first(name=name)

            if l is None:
                print cformat('%{yellow!}*** WARNING')
                print cformat("%{{yellow!}}***%{{reset}} Location '{}' does not exist. Skipped equipment: {}".format(
                    name, eqs
                ))
                continue

            l.equipment_types.extend(EquipmentType(name=x) for x in eqs)
            print cformat('- [%{cyan}{}%{reset}] {}').format(name, eqs)
            db.session.add(l)
        db.session.commit()
        print

        print cformat('%{white!}migrating vc equipment')
        for name, vcs in vc.iteritems():
            l = Location.find_first(name=name)

            if l is None:
                print cformat('%{yellow!}*** WARNING')
                print cformat("%{{yellow!}}***%{{reset}} Location '{}' does not exist. Skipped VC equipment: {}".format(
                    name, vcs
                ))
                continue

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

        for old_room_id, old_room in self.rb_root['Rooms'].iteritems():
            l = Location.find_first(name=old_room._locationName)

            if l is None:
                print cformat('%{yellow!}*** WARNING')
                print cformat("%{{yellow!}}***%{{reset}} Location '{}' does not exist. Skipped room '{}'".format(
                    old_room._locationName, old_room.id
                ))
                continue

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
                notification_for_assistance=getattr(old_room, 'resvNotificationAssistance', False),

                reservations_need_confirmation=old_room.resvsNeedConfirmation,

                telephone=convert_to_unicode(getattr(old_room, 'telephone', None)),
                key_location=convert_to_unicode(getattr(old_room, 'whereIsKey', None)),

                capacity=getattr(old_room, 'capacity', None),
                surface_area=getattr(old_room, 'surfaceArea', None),
                latitude=getattr(old_room, 'latitude', None),
                longitude=getattr(old_room, 'longitude', None),

                comments=convert_to_unicode(getattr(old_room, 'comments', None)),

                owner_id=self.merged_avatars.get(old_room.responsibleId, old_room.responsibleId),

                is_active=old_room.isActive,
                is_reservable=old_room.isReservable,
                max_advance_days=int(old_room.maxAdvanceDays) if getattr(old_room, 'maxAdvanceDays', None) else None
            )

            print cformat('- [%{cyan}{}%{reset}] %{grey!}{:4}%{reset}  %{green!}{}%{reset}').format(l.name, r.id,
                                                                                                    r.name)

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

            if self.photo_path:
                try:
                    with open(os.path.join(self.photo_path, 'large_photos',
                                           get_canonical_name_of(old_room) + '.jpg'), 'rb') as f:
                        large_photo = f.read()
                except Exception:
                    large_photo = None

                try:
                    with open(os.path.join(self.photo_path, 'small_photos',
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

    def migrate_reservations(self):
        print cformat('%{white!}migrating reservations')
        i = 1
        for rid, v in self.rb_root['Reservations'].iteritems():
            room = Room.get(v.room.id)
            if room is None:
                print cformat('  %{red!}skipping resv for dead room {0.room.id}: {0.id} ({0._utcCreatedDT})').format(v)
                continue

            repeat_frequency, repeat_interval = RepeatMapping.convert_legacy_repeatability(v.repeatability)
            booked_for_id = getattr(v, 'bookedForId', None)

            r = Reservation(
                id=v.id,
                created_dt=as_utc(v._utcCreatedDT),
                start_dt=utc_to_local(v._utcStartDT),
                end_dt=utc_to_local(v._utcEndDT),
                booked_for_id=self.merged_avatars.get(booked_for_id, booked_for_id) or None,
                booked_for_name=convert_to_unicode(v.bookedForName),
                contact_email=convert_to_unicode(v.contactEmail),
                contact_phone=convert_to_unicode(getattr(v, 'contactPhone', None)),
                created_by_id=self.merged_avatars.get(v.createdBy, v.createdBy) or None,
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
                event = self.zodb_root['conferences'].get(event_id)
                if event:
                    # For some stupid reason there are bookings in the database which have a completely unrelated parent
                    guids = getattr(event, '_Conference__roomBookingGuids', [])
                    if any(int(x.id) == v.id for x in guids if x.id is not None):
                        r.event_id = int(event_id)
                    else:
                        print cformat('  %{red}event {} does not contain booking {}').format(event_id, v.id)

            print cformat('- [%{cyan}{}%{reset}/%{green!}{}%{reset}]  %{grey!}{}%{reset}  {}').format(
                room.location_name,
                room.name,
                r.id,
                r.created_dt.date())

            room.reservations.append(r)
            db.session.add(room)
            i = (i + 1) % 1000
            if not i:
                db.session.commit()
        db.session.commit()

    def migrate_blockings(self):
        state_map = {
            None: BlockedRoom.State.pending,
            False: BlockedRoom.State.rejected,
            True: BlockedRoom.State.accepted
        }

        print cformat('%{white!}migrating blockings')
        for old_blocking_id, old_blocking in self.rb_root['RoomBlocking']['Blockings'].iteritems():
            b = Blocking(
                id=old_blocking.id,
                created_by_id=self.merged_avatars.get(old_blocking._createdBy, old_blocking._createdBy),
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
                    principal_id = int(self.merged_avatars.get(old_principal._id, old_principal._id))
                    principal_type = 'User'
                else:
                    principal_type = 'Group'
                bp = BlockingPrincipal(_principal=[principal_type, principal_id])
                b._allowed.add(bp)
                print cformat(u'  %{blue!}Allowed:%{reset} {}({})').format(bp.entity_type, bp.entity_id)
            db.session.add(b)
        db.session.commit()
