import os
from argparse import ArgumentParser
from pprint import pprint

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
    pass


def get_canonical_name_of(old_room):
    return '{}-{}-{}-{}'.format(
        old_room._locationName,
        old_room.building,
        old_room.floor,
        old_room.roomNr,
    )


def migrate(main_root, rb_root, photo_path):

    default_location_name = main_root['DefaultRoomBookingLocation']

    for old_location in main_root['RoomBookingLocationList']:
        l = Location(
            name=old_location.friendlyName,
            support_emails=','.join(old_location._avcSupportEmails),
            is_default=(old_location.friendlyName == default_location_name)
        )

        for old_aspect in old_location.aspects.values():
            a = Aspect(
                name=old_aspect.name,
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

        db.session.add(l)

    db.session.commit()  # commit locations + aspects

    for old_room_id, old_room in rb_root['Rooms'].iteritems():
        r = Room(
            id=old_room_id,
            name=(old_room._name or ''),
            site=old_room.site,
            division=old_room.site,
            building=old_room.building,
            floor=old_room.floor,
            number=old_room.roomNr,

            notification_for_start=convert_room_notification_for_start(
                old_room.resvStartNotification,
                old_room.resvStartNotificationBefore
            ),
            notification_for_end=old_room.resvEndNotification,
            notification_for_responsible=old_room.resvNotificationToResponsible,
            notification_for_assistance=old_room.resvNotificationAssistance,

            reservations_need_confirmation=old_room.resvsNeedConfirmation,

            telephone=old_room.telephone,
            key_location=old_room.whereIsKey,

            capacity=old_room.capacity,
            surface_area=old_room.surfaceArea,
            latitude=old_room.latitude,
            longitude=old_room.longitude,

            comments=old_room.comments,

            owner_id=old_room.responsibleId,

            is_active=old_room.isActive,
            is_reservable=old_room.isReservable,
            max_advance_days=convert_room_max_advance_days(old_room.maxAdvanceDays),
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
            # TODO: stopped here
            # e = RoomEquipment(name=old_equipment)
            pass

        l = Location.getLocationByName(old_room._locationName)
        l.rooms.append(r)

        db.session.add(l)
        db.session.commit()

    #     s, e, v = set(), set(), set()

    #     if hasattr(old_room, 'customAtts'):
    #         for k in old_room.customAtts.keys():
    #             s.add(k)

    #     for k in old_room._equipment.split('`'):
    #         e.add(k)

    #     for k in old_room.avaibleVC:
    #         v.add(k)

    # print 'customAtts:'
    # pprint(s)
    # print
    # print '_equipment:'
    # pprint(e)
    # print
    # print 'avaibleVC:'
    # pprint(v)

    # for k, v in rb_root['Reservations'].iteritems():
    #     repeat_unit, repeat_step = convert_reservation_repeatibility(v.repeatability)

    #     r = Reservation(
    #         id=v.id,
    #         booked_for_id=v.bookedForId,
    #         booked_for_name=v.bookedForName,
    #         contact_email=v.contactEmail,
    #         contact_phone=v.contactPhone,
    #         created_by=v.createdBy,
    #         is_cancelled=v.isCancelled,
    #         is_confirmed=v.isConfirmed,
    #         is_rejected=v.isRejected,
    #         reason=v.reason,
    #         repeat_unit=repeat_unit,
    #         repeat_step=repeat_step
    #     )

    #     db.session.add(r)
    # db.session.commit()

def main():
    main_root, rb_root, app = setup(
        '~/data_backup.fs',
        '~/rb.fs',
        'sqlite:///~/data.db'
    )

    with app.app_context():
        db.create_all()
        migrate(main_root, rb_root, '~/images/')

if __name__ == '__main__':
    main()
