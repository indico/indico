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
from argparse import ArgumentParser
from datetime import datetime
from pprint import pprint
from time import mktime, strptime

from flask import Flask
from ZODB import DB, FileStorage

from indico.core.db import db
from indico.modules.rb.models import *


def setup(main_zodb_path, rb_zodb_path, sqlalchemy_uri):
    app = Flask('migration')
    app.config['SQLALCHEMY_DATABASE_URI'] = sqlalchemy_uri
    db.init_app(app)

    main_root = DB(FileStorage.FileStorage(main_zodb_path)).open().root()
    rb_root = DB(FileStorage.FileStorage(rb_zodb_path)).open().root()

    return main_root, rb_root, app


def teardown():
    pass


def convert_reservation_repeatibility(old):
    return [(RepeatUnit.DAY, 1),
            (RepeatUnit.WEEK, 1),
            (RepeatUnit.WEEK, 2),
            (RepeatUnit.WEEK, 3),
            (RepeatUnit.MONTH, 1),
            (RepeatUnit.NEVER, 0)][
            [0, 1, 2, 3, 4, None].index(old)]


def convert_room_notification_for_start(flag, before):
    return before if flag else 0


def convert_room_max_advance_days(old):
    return int(old) if old else 30


def get_canonical_name_of(old_room):
    return '{}-{}-{}-{}'.format(
        old_room._locationName,
        old_room.building,
        old_room.floor,
        old_room.roomNr
    )


def get_room_id(guid):
    """ location | room_id """
    return int(guid.split('|')[1].strip())


def convert_date(ds):
    if isinstance(ds, str):
        struct = strptime(ds, '%d %b %Y %H:%M')
        return datetime.fromtimestamp(mktime(struct))
    return ds


def convert_to_unicode(val):
    if isinstance(val, str):
        try:
            return unicode(val, 'utf-8')
        except:
            return unicode(val, 'latin1')
    elif isinstance(val, unicode):
        return val
    elif val is None:
        return u''
    raise RuntimeError('Unexpected type is found for unicode conversion')


def migrate_locations(main_root, rb_root):

    default_location_name = main_root['DefaultRoomBookingLocation']
    custom_attributes_dict = rb_root['CustomAttributesList']

    for old_location in main_root['RoomBookingLocationList']:
        # create location
        l = Location(
            name=convert_to_unicode(old_location.friendlyName),
            support_emails=convert_to_unicode(','.join(old_location._avcSupportEmails)),
            is_default=(old_location.friendlyName == default_location_name)
        )

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

            l.aspects.append(a)
            if old_aspect.defaultOnStartup:
                l.default_aspect = a

        # add custom attributes
        if l.name in custom_attributes_dict:
            for ca in custom_attributes_dict[l.name]:
                name = convert_to_unicode(ca['name'])
                k = LocationAttributeKey.getKeyByName(name)
                if not k:
                    k = LocationAttributeKey(name=name)
                a = LocationAttribute()
                a.value = dict((k, v) for k, v in ca.iteritems() if k != 'name')
                k.attributes.append(a)
                l.attributes.append(a)

        # add created location
        db.session.add(l)
        db.session.commit()


def migrate_rooms(main_root, rb_root, photo_path):

    for old_room_id, old_room in rb_root['Rooms'].iteritems():

        r = Room(
            id=old_room_id,
            name=convert_to_unicode(old_room._name),
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

        for old_bookable_time in old_room.getDailyBookablePeriods():
            b = BookableTime(
                start_time=old_bookable_time._startTime,
                end_time=old_bookable_time._endTime,
            )
            r.bookable_times.append(b)

        for old_nonbookable_date in old_room.getNonBookableDates():
            d = NonBookableDate(
                start_date=old_nonbookable_date._startDate,
                end_date=old_nonbookable_date._endDate
            )
            r.nonbookable_dates.append(d)

        if photo_path:
            try:
                with open(os.path.join(
                    photo_path,
                    'large_photos',
                    get_canonical_name_of(old_room) + '.jpg'), 'rb') as f:
                    large_photo = f.read()
            except:
                large_photo = None

            try:
                with open(os.path.join(
                    photo_path,
                    'small_photos',
                    get_canonical_name_of(old_room) + '.jpg'), 'rb') as f:
                    small_photo = f.read()
            except:
                small_photo = None

            if large_photo and small_photo:
                p = Photo(
                    large_content=large_photo,
                    small_content=small_photo
                )
            r.photos.append(p)

        for old_equipment in old_room._equipment.split('`'):
            if old_equipment:
                e = RoomEquipment.getEquipmentByName(old_equipment)
                if e:
                    r.equipments.append(e)
                else:
                    r.equipments.append(RoomEquipment(name=old_equipment))

        for k, v in getattr(old_room, 'customAtts', {}).iteritems():
            name = convert_to_unicode(k)
            k = RoomAttributeKey.getKeyByName(name)
            if not k:
                k = RoomAttributeKey(name=name)
            a = RoomAttribute(value=convert_to_unicode(v))
            k.attributes.append(a)
            r.attributes.append(a)

        a = RoomAttributeKey.getKeyByName('Live Webcast') or RoomAttributeKey(name='Live Webcast')
        for old_child_custom_attribute in getattr(old_room, 'avaibleVC', []):
            child_name = convert_to_unicode(old_child_custom_attribute)
            ck = RoomAttributeKey.getKeyByName(child_name)
            if not ck:
                ck = RoomAttributeKey(name=child_name)
            ca = RoomAttribute(value=u'')
            ck.attributes.append(ca)
            for attr in a.attributes:
                attr.children.append(ca)
            r.attributes.append(ca)

        l = Location.getLocationByName(old_room._locationName)
        l.rooms.append(r)
        db.session.add(l)
        db.session.commit()


def migrate_reservations(main_root, rb_root):

    extra_attributes = ['usesAVC', 'needsAVCSupport', 'needsAssistance']

    for k in extra_attributes:
        db.session.add(ReservationAttributeKey(name=k))

    keys = set(k for r in rb_root['Reservations'].values()
               for k in getattr(r, 'useVC', []))
    for k in keys:
        db.session.add(ReservationAttributeKey(name=k))
    db.session.commit()

    for rid, v in rb_root['Reservations'].iteritems():

        repeat_unit, repeat_step = convert_reservation_repeatibility(v.repeatability)

        r = Reservation(
            id=v.id,
            created_at=convert_date(v._utcCreatedDT),
            start_date=convert_date(v._utcStartDT),
            end_date=convert_date(v._utcEndDT),
            booked_for_id=(v.bookedForId or '1073'),
            booked_for_name=convert_to_unicode(v.bookedForName),
            contact_email=v.contactEmail,
            contact_phone=v.contactPhone,
            created_by=(v.createdBy or '1073'),
            is_cancelled=v.isCancelled,
            is_confirmed=v.isConfirmed,
            is_rejected=v.isRejected,
            reason=convert_to_unicode(v.reason),
            repeat_unit=repeat_unit,
            repeat_step=repeat_step
        )

        if getattr(v, 'resvHistory', None):
            for h in v.resvHistory._entries:
                l = ReservationEditLog(
                    timestamp=convert_date(h._timestamp),
                    avatar_id=h._responsibleUser,
                    info=convert_to_unicode('```'.join(h._info))
                )
                r.edit_logs.append(l)

        for d in v._excludedDays:
            ex = ReservationExcludedDay(
                start_date=convert_date(d),
                end_date=convert_date(d)
            )
            r.excluded_dates.append(ex)

        for e in extra_attributes:
            a = ReservationAttribute(value=getattr(v, e, False) or False)
            k = ReservationAttributeKey.getKeyByName(e)
            k.attributes.append(a)
            r.attributes.append(a)

        for e in getattr(v, 'useVC', []):
            a = ReservationAttribute(value=True)
            k = ReservationAttributeKey.getKeyByName(e)
            k.attributes.append(a)
            r.attributes.append(a)

        room = Room.getRoomById(v.room.id)
        room.reservations.append(r)
        db.session.add(room)
        db.session.commit()


def migrate_blockings(main_root, rb_root):

    for old_blocking_id, old_blocking in rb_root['RoomBlocking']['Blockings'].iteritems():
        b = Blocking(
            id=old_blocking.id,
            created_by=old_blocking._createdBy,
            created_at=old_blocking._utcCreatedDT,
            start_date=old_blocking.startDate,
            end_date=old_blocking.endDate,
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


def migrate(*args):
    migrate_locations(*args[:-1])
    migrate_rooms(*args)
    migrate_reservations(*args[:-1])
    migrate_blockings(*args[:-1])


def main(*args):
    main_root, rb_root, app = setup(*args[:3])

    with app.app_context():
        db.create_all()
        migrate(main_root, rb_root, args[-1])


if __name__ == '__main__':
    parser = ArgumentParser(prog='migration')
    parser.add_argument('main', help='main zodb storage path')
    parser.add_argument('rb', help='room booking zodb file storage path')
    parser.add_argument('uri', help='sqlalchemy database uri')
    parser.add_argument('-p', '--photo', help='photos path')

    args = parser.parse_args()
    main(args.main, args.rb, args.uri, args.photo)
