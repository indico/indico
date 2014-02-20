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

"""
Schema of a room
"""

from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from sqlalchemy import (
    and_,
    func,
    event,
    exists,
    extract,
    not_,
    or_,
    null,
    type_coerce
)
from sqlalchemy.dialects.postgresql.base import array, ARRAY as sa_array
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import aliased
from sqlalchemy.sql import select
from sqlalchemy.sql.expression import cast, literal
from sqlalchemy.types import (
    Date as sa_date,
    DateTime as sa_datetime,
    Integer as sa_integer,
    Text as sa_string,
    Time as sa_time
)

from MaKaC.webinterface import urlHandlers as UH
from MaKaC.accessControl import AccessWrapper
from MaKaC.common.Locators import Locator
from MaKaC.errors import MaKaCError
from MaKaC.user import (
    Avatar,
    AvatarHolder,
    GroupHolder
)

from indico.core.db import db, time_diff, greatest, least
from indico.modules.rb.models import utils
from indico.modules.rb.models.attribute_keys import AttributeKey
from indico.modules.rb.models.blockings import Blocking
from indico.modules.rb.models.blocked_rooms import BlockedRoom
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.room_attributes import RoomAttribute
from indico.modules.rb.models.room_bookable_times import BookableTime
from indico.modules.rb.models.room_equipments import (
    RoomEquipment,
    RoomEquipmentAssociation
)
from indico.modules.rb.models.room_nonbookable_dates import NonBookableDate

from indico.util.i18n import _

from .utils import Serializer


class RoomKind(object):
    BASIC, MODERATED, PRIVATE = 'basicRoom', 'moderatedRoom', 'privateRoom'


class Room(db.Model, Serializer):
    __tablename__ = 'rooms'
    __public__ = [
        'id', 'name', 'location_name', 'floor', 'number', 'building',
        'booking_url', 'capacity', 'comments', 'owner_id',
        'large_photo_url', 'small_photo_url', 'has_photo', 'is_active',
        'is_reservable', 'is_public', 'is_auto_confirm', 'marker_description',
        'needs_video_conference_setup', 'has_webcast_recording',
        'has_booking_groups', 'kind'
    ]
    __calendar_public__= [
        'id', 'building', 'name', 'floor', 'number', 'kind', 'booking_url'
    ]

    # columns

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    # location
    location_id = db.Column(
        db.Integer,
        db.ForeignKey('locations.id'),
        nullable=False
    )
    # user-facing identifier of the room
    name = db.Column(
        db.String,
        nullable=False
    )
    # address
    site = db.Column(
        db.String,
        default=''
    )
    division = db.Column(
        db.String
    )
    building = db.Column(
        db.String,
        nullable=False
    )
    floor = db.Column(
        db.String,
        default='',
        nullable=False
    )
    number = db.Column(
        db.String,
        default='',
        nullable=False
    )
    # notifications
    notification_for_start = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )
    notification_for_end = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    notification_for_responsible = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    notification_for_assistance = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    reservations_need_confirmation = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    # extra info about room
    telephone = db.Column(
        db.String
    )
    key_location = db.Column(
        db.String
    )
    capacity = db.Column(
        db.Integer,
        default=20
    )
    surface_area = db.Column(
        db.Integer
    )
    latitude = db.Column(
        db.String
    )
    longitude = db.Column(
        db.String
    )
    comments = db.Column(
        db.String
    )
    # just a pointer to avatar
    owner_id = db.Column(
        db.String,
        nullable=False
    )
    # reservations
    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    is_reservable = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    max_advance_days = db.Column(
        db.Integer,
        nullable=False,
        default=30
    )

    # relationships

    attributes = db.relationship(
        'RoomAttributeAssociation',
        backref='room',
        # cascade='all, delete-orphan',
        lazy='dynamic'
    )

    blocked_rooms = db.relationship(
        'BlockedRoom',
        backref='room',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    bookable_times = db.relationship(
        'BookableTime',
        backref=db.backref(
            'room',
            order_by='BookableTime.start_time'
        ),
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    equipments = db.relationship(
        'RoomEquipment',
        secondary=RoomEquipmentAssociation,
        backref='rooms',
        lazy='dynamic'
    )

    nonbookable_dates = db.relationship(
        'NonBookableDate',
        backref='room',
        order_by=NonBookableDate.end_date.desc(),
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    photos = db.relationship(
        'Photo',
        backref='room',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    reservations = db.relationship(
        'Reservation',
        backref='room',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    # many to many deleter
    # @event.listens_for(scoped_session, 'after_flush')

    # core

    def __str__(self):
        s = """
               id: {id}
         isActive: {is_active}

             room: {name}

         building: {building}
            floor: {floor}
           roomNr: {number}
     isReservable: {is_reservable}
rNeedConfirmation: {reservations_need_confirmation}
startNotification: {notification_for_start}
  endNotification: {notification_for_end}
notificationToResponsible: {notification_for_responsible}
notificationAssistance: {notification_for_assistance}

             site: {site}
         capacity: {capacity}
      surfaceArea: {surface_area}
         division: {division}

        telephone: {telephone}
       whereIsKey: {key_location}
         comments: {comments}
    responsibleId: {owner_id}
        equipment: """
        return "{}{}\n".format(utils.formatString(s, self),
                               self.getVerboseEquipment())

    def __cmp__(self, other):
        if not (self and other):
            return cmp(
                1 if self else None,
                1 if other else None
            )
        if self.id == other.id:
            return 0

        return (cmp(self.location.name, other.location.name) or
                cmp(self.building, other.building) or
                cmp(self.floor, other.floor) or
                cmp(self.number, other.number) or
                cmp(self.name, other.name))

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __repr__(self):
        return '<Room({0}, {1}, {2})>'.format(
            self.id,
            self.location_id,
            self.name
        )

    @property
    def location_name(self):
        return self.location.name

    @property
    def booking_url(self):
        return str(UH.UHRoomBookingBookingForm.getURL(target=self))

    @property
    def details_url(self):
        return str(UH.UHRoomBookingRoomDetails.getURL(target=self))

    @property
    def _photo_id(self):
        p = self.photos.first()
        return p.id if p else 'NoPhoto'

    @property
    def large_photo_url(self):
        return str(UH.UHRoomPhoto.getURL(self._photo_id))

    @property
    def small_photo_url(self):
        return str(UH.UHRoomPhotoSmall.getURL(self._photo_id))

    @property
    def has_photo(self):
        return self.photos.count() > 0

    @property
    def is_public(self):
        return self.is_reservable and not self.has_booking_groups

    @property
    def is_auto_confirm(self):
        return not self.reservations_need_confirmation

    @property
    def marker_description(self):
        infos = []

        infos.append('{capacity} {label}'.format(
            capacity=self.capacity,
            label=(_('person'), _('people'))[self.capacity > 1 or self.capacity == 0]
        ))
        infos.append((_('private'),
                      _('public'))[self.is_reservable and not self.has_booking_groups])
        infos.append((_('auto-confirmation'),
                      _('needs confirmation'))[self.reservations_need_confirmation])
        if self.needs_video_conference_setup:
            infos.append(_('video conference'))

        return ', '.join(infos)

    @property
    def guid(self):
        return 'SHOULD BE REMOVED'

    def getEquipmentByName(self, equipment_name):
        return self.equipments\
                   .filter_by(name=equipment_name)\
                   .first()

    def has_equipment(self, equipment_name):
        return self.getEquipmentByName(equipment_name) is not None

    @property
    def needs_video_conference_setup(self):
        return self.has_equipment('Video conference')

    @property
    def has_webcast_recording(self):
        return self.has_equipment('Webcast/Recording')

    @property
    def available_video_conference(self):
        # return children of 'Video conference' equipment
        pass

    def getAttributeByName(self, attribute_name):
        return self.attributes\
                   .join(RoomAttribute)\
                   .filter(RoomAttribute.name == attribute_name)\
                   .first()

    def has_attribute(self, attribute_name):
        return self.getAttributeByName(attribute_name) is not None

    @property
    def has_booking_groups(self):
        return self.has_attribute('Allowed Booking Group')

    @property
    def kind(self):
        if not self.is_reservable or self.has_booking_groups:
            roomCls = 'privateRoom'
        elif self.is_reservable and self.reservations_need_confirmation:
            roomCls = 'moderatedRoom'
        elif self.is_reservable:
            roomCls = 'basicRoom'
        return roomCls

    def getLocator(self):
        locator = Locator()
        locator['roomLocation'] = self.location.name
        locator['roomID'] = self.id
        return locator

    def getFullName(self):
        return '{}-{}-{}-{}'.format(
            self.building,
            self.floor,
            self.number,
            self.name
        )

    def updateName(self):
        if not self.name and self.building and self.floor and self.number:
            self.name = '{}-{}-{}'.format(
                self.building,
                self.floor,
                self.number
            )

    def getAccessKey(self):
        return ''

    # rooms

    @staticmethod
    def getRoomWithDefaults():
        return Room(
            capacity=20,
            is_active=True,
            is_reservable=True,
            reservations_need_confirmation=False,
            notification_for_start=0,
            notification_for_end=False,
            notification_for_responsible=False,
            notification_for_assistance=False,
            max_advance_days=30
        )

    @staticmethod
    def getRoomById(rid):
        return Room.query.get(rid)

    @staticmethod
    def getRoomsByIds(id_list):
        q = Room.query
        if id_list and -1 not in id_list:
            q = q.filter(Room.id.in_(id_list))
        return q.all()

    @staticmethod
    @utils.filtered
    def filterRooms(**filters):
        return Room, Room.query

    @staticmethod
    def getRooms(only_public=False):
        # TODO: not complete yet
        return Room.query.all()

    @staticmethod
    def getRoomsWithMaxCapacity():
        from .locations import Location

        q = Room.query.subquery()

        max_capacity_row_columns = [
            (func.coalesce(func.max(Room.capacity), 0) if c.name == 'capacity'
            else (func.coalesce(func.max(Room.id), 0) + 1 if c.name == 'id'
            else null())).label(c.name)
            for c in q.selectable.columns
        ]

        records = Room.query\
                      .select_from(q)\
                      .union(
                          Room.query
                              .with_entities(*max_capacity_row_columns)
                      )\
                      .outerjoin(Location, Location.id == Room.location_id)\
                      .with_entities(Room)\
                      .order_by(
                        Location.name,
                        Room.building,
                        Room.floor,
                        Room.number,
                        Room.name
                      )\
                      .all()
        return records[:-1], records[-1].capacity

    @staticmethod
    def getRoomsByName(name):
        return Room.getRooms(name=name)

    @staticmethod
    def getRoomByName(name):
        return Room.query.filter_by(name=name).first()

    # TODO
    def isAvailable(self, r):
        return len(r.getCollisions()) == 0

    def getResponsible(self):
        return AvatarHolder().getById(self.owner_id)

    def getResponsibleName(self):
        r = self.getResponsible()
        if r:
            return r.getFullName()

    # reservations

    @utils.filtered
    def filterReservations(self, **filters):
        return Reservation, self.reservations

    def doesHaveLiveReservations(self):
        return self.reservations.filter_by(
            is_live=True,
            is_cancelled=False,
            is_rejected=False
        ).count() > 0

    def getLiveReservations(self):
        return self.filterReservations(
            is_live=True,
            is_cancelled=False,
            is_rejected=False
        )

    def removeReservations(self):
        del self.reservations[:]

    @staticmethod
    def isAvatarResponsibleForRooms(avatar):
        return Room.query.filter_by(owner_id=avatar.id).count() > 0

    @staticmethod
    def getRoomsOfUser(avatar):
        return Room.query.filter_by(owner_id=avatar.getId()).all()

    def getLocationName(self):
        return self.location.name

    @staticmethod
    def getFilteredReservationsInSpecifiedRooms(f, avatar=None):
        q = Room.query\
                .outerjoin(Reservation, Room.id == Reservation.room_id)\
                .join(ReservationOccurrence,
                      Reservation.id == ReservationOccurrence.reservation_id)\
                .filter(
                    or_(
                        and_(
                            ReservationOccurrence.start >= f.start_date.data,
                            ReservationOccurrence.start <= f.end_date.data,
                        ),
                        and_(
                            ReservationOccurrence.end >= f.start_date.data,
                            ReservationOccurrence.end <= f.end_date.data,
                        )
                    )
                )

        if f.is_only_my_rooms.data and avatar:
            q = q.filter(Room.owner_id == avatar.id)
        elif f.room_id_list.data and -1 not in f.room_id_list.data:
            q = q.filter(Room.id.in_(f.room_id_list.data))

        if f.is_only_bookings.data:
            q = q.filter(Reservation.is_confirmed == True)
        if f.is_only_pre_bookings.data:
            q = q.filter(Reservation.is_confirmed == False)

        if f.is_only_mine.data and avatar:
            q = q.filter(Reservation.booked_for_id == avatar.id)
        elif f.booked_for_name.data:
            qs = u'%{}%'.format(f.booked_for_name.data)
            q = q.filter(Reservation.booked_for_name.ilike(qs))

        if f.reason.data:
            qs = u'%{}%'.format(f.reason.data)
            q = q.filter(Reservation.reason.ilike(qs))

        if f.is_rejected.data:
            q = q.filter(
                or_(
                    Reservation.is_rejected == True,
                    ReservationOccurrence.is_rejected == True
                )
            )
        if f.is_cancelled.data:
            q = q.filter(
                or_(
                    Reservation.is_cancelled == True,
                    ReservationOccurrence.is_cancelled == True
                )
            )
        if f.is_archival.data:
            q = q.filter(Reservation.is_archival == True)
        if f.uses_video_conference.data:
            q = q.filter(Reservation.uses_video_conference == True)
        if f.needs_video_conference_setup.data:
            q = q.filter(Reservation.needs_video_conference_setup == True)
        if f.needs_general_assistance.data:
            q = q.filter(Reservation.needs_general_assistance == True)
        return q.all()

    @staticmethod
    def getReservationsForAvailability(start_date, end_date, room_id_list):
        from .locations import Location

        date_query = db.session.query(
                        cast(
                            func.generate_series(
                                start_date.date(),
                                end_date.date(),
                                timedelta(1)
                            ),
                            sa_date
                        ).label('available_date')
                    )\
                    .subquery()\

        # def get_exclude_null_query(attr, kind):
        #     # return db.session\
        #     #          .query(func.array_agg('x'))\
        #     #          .select_from(func.unnest(func.array_agg(attr).alias('x')))\
        #     #          .correlate(Reservation)\
        #     #          .filter('x != null')\
        #     #          .subquery()
        #     print kind, '==================='
        #     return select([type_coerce(
        #         func.array_agg('x'),
        #         sa_array(kind, as_tuple=True))])\
        #     .select_from(
        #         func.unnest(func.array_agg(attr)).alias('x')
        #     )\
        #     .where('x != None')\
        #     .as_scalar()

        def coerce_as_tuple(attr, kind=None):
            return type_coerce(
                func.array_agg(attr),
                sa_array(kind or attr.type, as_tuple=True)
            )

        return db.session\
                 .query()\
                 .select_from(date_query)\
                 .with_entities(
                    date_query.c.available_date,
                    Room,
                    func.min(Location.name),
                    func.min(Blocking.id),
                    func.min(Blocking.reason),
                    func.min(Blocking.created_by),
                    coerce_as_tuple(Reservation.id),
                    # coerce_as_tuple(Reservation.booking_reason),
                    coerce_as_tuple(Reservation.booked_for_name),
                    coerce_as_tuple(Reservation.booked_for_name),
                    coerce_as_tuple(Reservation.is_confirmed),
                    coerce_as_tuple(cast(ReservationOccurrence.start, sa_time)),
                    coerce_as_tuple(cast(ReservationOccurrence.end, sa_time))
                )\
                .outerjoin(
                    Location,
                    literal(1) == 1  # cartesian product
                )\
                .outerjoin(
                    Room,
                    Location.rooms
                )\
                .outerjoin(
                    Reservation,
                    Room.reservations
                )\
                .outerjoin(
                    ReservationOccurrence,
                    and_(
                        Reservation.occurrences,
                        date_query.c.available_date == cast(ReservationOccurrence.start, sa_date)
                    )
                )\
                .outerjoin(
                    BlockedRoom,
                    BlockedRoom.room_id == Room.id
                )\
                .outerjoin(
                    Blocking,
                    Blocking.id == BlockedRoom.blocking_id
                )\
                .correlate(date_query)\
                .filter(
                    Room.id.in_(room_id_list),
                )\
                .group_by(date_query.c.available_date, Room.id)\
                .order_by(date_query.c.available_date, Room.name)\
                .all()

    @staticmethod
    def getReservationsForAvailability2(start_date, end_date, room_id_list):
        date_query = db.session.query(
                        cast(
                            func.generate_series(
                                start_date.date(),
                                end_date.date(),
                                timedelta(1)
                            ),
                            sa_date
                        ).label('available_date')

                    )\
                    .subquery()\

        return db.session\
                 .query(date_query.c.available_date)\
                 .select_from(date_query)\
                 .correlate(date_query)\
                 .filter(
                    date_query.c.available_date != date(2014, 2, 18)
                 )\
                 .all()

    # equipments

    @utils.filtered
    def filterEquipments(self, **filters):
        return RoomEquipment, self.equipments

    def getEquipmentNames(self):
        return self.equipment_names

    def getEquipmentIds(self):
        return self.equipments.with_entities(RoomEquipment.id).all()

    def getEquipmentByName(self, name):
        return self.equipments.filter_by(name=name).first()

    def addEquipments(self, equipment_names):
        self.equipment_names.extend(equipment_names)

    def addEquipment(self, equipment_name):
        eq = self.getEquipmentByName(equipment_name)
        if not eq:
            self.equipment_names.append(equipment_name)

    def removeEquipments(self, equipment_names):
        del self.equipments[:]

    def removeEquipment(self, equipment_name):
        self.equipments.filter_by(name=equipment_name).delete()

    # def hasEquipment(self, eq):
    #     return self.equipments.get(eq.id) is not None

    def hasEquipment(self, name):
        return any(eq.name == name for eq in self.equipments)

    def clearEquipments(self):
        for eq in self.equipments.all():
            self.equipments.remove(eq)

    def setEquipments(self, eqs):
        if self.id:
            self.clearEquipments()
        self.equipments.extend(eqs)

    def hasEquipments(self, names):
        def has(name):
            return any(map(lambda e: e.lower.find(name) != -1, self.equipment_names))
        return all(map(lambda name: has(name), names))

    def needsVideoConferenceSetup(self):
        return self.hasEquipment('Video Conference')

    def hasWebcastRecording(self):
        return self.hasEquipment('Webcast/Recording')

    def getVerboseEquipment(self):
        return self.equipments\
                   .with_entities(func.array_to_string(func.array_agg(RoomEquipment.name), ', '))\
                   .scalar()
        # return (self.equipments
        #         .with_entities(func.group_concat(RoomEquipment.name))
        #         .scalar())

    def isCloseToBuilding(self):
        raise NotImplementedError('todo')

    def belongsTo(self, avatar):
        raise NotImplementedError('todo')

    # bookable times

    def getBookableTimes(self):
        return self.bookable_times.all()

    def getBookableTimesOrDefault(self):
        return self.getBookableTimes() or \
              [BookableTime(start_time=None, end_time=None)]

    def addBookableTime(self, bookable_time):
        self.bookable_times.append(bookable_time)

    # TODO: better remove
    def clearBookableTimes(self):
        for bt in self.bookable_times.all():
            self.bookable_times.remove(bt)

    def setBookableTimes(self, bookable_times):
        self.clearBookableTimes()
        self.bookable_times.extend(bookable_times)

    # nonbookable dates

    def getNonBookableDates(self, skip_past=False):
        q = self.nonbookable_dates
        if skip_past:
            q = q.filter(NonBookableDate.start_date >= datetime.utcnow())
        return q.all()

    def getNonBookableDatesOrDefault(self):
        return self.getNonBookableDates() or \
               [NonBookableDate(start_date=None, end_date=None)]

    def addNonBookableDate(self, nonbookable_date):
        self.nonbookable_dates.append(nonbookable_date)

    # TODO: better remove
    def clearNonBookableDates(self):
        for nbd in self.nonbookable_dates.all():
            self.nonbookable_dates.remove(nbd)

    def setNonBookableDates(self, nonbookable_dates):
        self.clearNonBookableDates()
        self.nonbookable_dates.extend(nonbookable_dates)

    # blocked rooms

    def getBlockedRoom(self, d):
        return (self.blocked_rooms
                    .join(BlockedRoom.blocking)
                    .filter(
                         Blocking.is_active_at(d),
                         BlockedRoom.is_active == True
                     )
                    .first())

    # attributes

    @utils.filtered
    def filterAttributes(self, **filters):
        return RoomAttribute, self.attributes

    # def getAttributeByName(self, name):
    #     attribute = (self.attributes
    #                      .with_entities(RoomAttribute)
    #                      .join(RoomAttribute.key)
    #                      .filter(AttributeKey.name == name)
    #                      .first())
    #     return attribute

    def getAttributeValueByName(self, name):
        attr =  self.getAttributeByName(name)
        if attr:
            return attr.value

    def containsText(self, text):
        for attr in dir(self):
            if not attr.startswith('_') and isinstance(getattr(self, attr), str):
                if getattr(self, attr).lower().find(text) != -1:
                    return True

        avatar = self.getResponsible()
        if text in avatar.getFullName().lower() or text in avatar.getEmail.lower():
            return True

        like_query_param = '%{}%'.format(text)
        return (self.equipments
                    .join(Room.attributes)
                    .filter(
                        exists().where(
                            or_(
                                RoomEquipment.name.ilike(like_query_param),
                                RoomAttribute.raw_data.ilike(like_query_param)
                            )
                        )
                    ).scalar())

    # TODO: %20 should go to config
    @hybrid_property
    def isGoodCapacity(self, capacity):
        if not self.capacity or self.capacity == 0:
            return False
        return abs(self.capacity - capacity) / float(self.capacity) <= 0.2

    # access checks

    def hasAllowedBookingGroups(self):
        return False
        # return self.getAttributeByName('Allowed Booking Group') is not None

    def canBeViewedBy(self, accessWrapper):
        """Room details are public - anyone can view."""
        return True

    @utils.accessChecked
    def canBeBookedByProcess(self, avatar, pre=False):
        """
        Execution for canBeBookedBy and canBePreBookedBy methods
        """
        if (self.is_active and self.is_reservable and
            (pre or not self.reservations_need_confirmation)):

            # TODO:
            # allowed_groups = self.getAttributeByName('Allowed Booking Group')
            allowed_groups = []
            if not allowed_groups or allowed_groups.contains(avatar):
                return True

        if not avatar:
            return False

        if avatar.isRBAdmin() or (self.isOwnedBy(avatar) and self.is_active):
            return True

        return False

    def canBeBookedBy(self, avatar):
        """
        Reservable rooms which does not require pre-booking can be booked by anyone.
        Other rooms - only by their responsibles.
        """
        return self.canBeBookedByProcess(avatar)

    def canBePreBookedBy(self, avatar):
        """
        Reservable rooms can be pre-booked by anyone.
        Other rooms - only by their responsibles.
        """
        return self.canBeBookedByProcess(avatar, pre=True)

    def canBeModifiedBy(self, accessWrapper):
        """Only admin can modify rooms."""
        if not accessWrapper:
            return False

        if isinstance(accessWrapper, AccessWrapper):
            avatar = accessWrapper.getUser()
            return avatar.isRBAdmin() if avatar else False
        elif isinstance(accessWrapper, Avatar):
            return accessWrapper.isRBAdmin()

        raise MaKaCError(_('canModify requires either AccessWrapper or Avatar object'))

    def canBeDeletedBy(self, accessWrapper):
        """Entity can modify is also capable of deletion"""
        return self.canBeModifiedBy(accessWrapper)

    def isOwnedBy(self, avatar):
        """
        Returns True if user is responsible for this room. False otherwise.
        """
        # legacy check, currently every room must be owned by someone
        if not self.responsible_id:
            return None
        if self.responsible_id == avatar.id:
            return True
        manager_groups = self.getAttributeByName('Manager Group')
        return manager_groups.contains(avatar)

    def getGroups(self, group_name):
        groups = GroupHolder.match({'name': group_name},
                                    exact=True, searchInAuthenticators=False)
        if groups:
            return groups
        return GroupHolder.match({'name': group_name}, exact=True)

    def getAllManagers(self):
        managers = set([self.responsible_id])
        manager_groups = self.getAttributeValueByName('Manager Group')
        for group_name in (manager_groups and manager_groups['is_equipped']):
            groups = self.getGroups(group_name)
            if groups and len(groups) == 1:
                managers |= set(groups[0].getMemberList())
        return managers

    def checkManagerGroupExistence(self):
        attribute = self.getAttributeByName('Manager Group')
        if attribute:
            for group_name in attribute.value.get('is_equipped', []):
                if not self.getGroups(group_name):
                    attribute.value['is_equipped'] = ['Error: unknown mailing list']
                    break

    def hasManagerGroup(self):
        attribute = self.getAttributeByName('Manager Group')
        return attribute and attribute.value.get('is_equipped', [])

    # def is_public(self):
    #     return self.is_reservable and not self.hasManagerGroup()

    def notifyAboutResponsibility( self ):
        """
        Notifies (e-mails) previous and new responsible about
        responsibility change. Called after creating/updating the room.
        """
        pass

    # statistics

    @staticmethod
    def getNumberOfRooms():
        return Room.query.count()

    @staticmethod
    def getNumberOfActiveRooms():
        return Room.query.filter_by(is_active=True).count()

    @staticmethod
    def getNumberOfReservableRooms():
        return Room.query.filter_by(is_reservable=True).count()

    def getTotalBookedTime(self, start_date=None, end_date=None):
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date + relativedelta(months=-1)

        return (
            self.reservations
                .join(ReservationOccurrence)
                .with_entities(
                    func.sum(
                        func.abs(
                            extract('epoch', ReservationOccurrence.start) - extract('epoch', ReservationOccurrence.end)
                        )
                    )
                )
                .filter(
                    # Reservation.is_cancelled == False,
                    # Reservation.is_rejected == False,
                    ReservationOccurrence.start >= start_date,
                    ReservationOccurrence.end <= end_date,
                    ReservationOccurrence.is_cancelled == False
                )
                .scalar()
        ) or 0

    def getTotalBookableTime(self, start_date=None, end_date=None):
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date + relativedelta(months=-1)

        # print (self.nonbookable_dates
        #         .with_entities(
        #             func.sum(
        #                 func.abs(
        #                     greatest(NonBookableDate.start_date, start_date) - least(NonBookableDate.end_date, end_date)
        #                 ) + 1
        #             )
        #         )
        #         .filter(
        #             or_(
        #                 and_(NonBookableDate.start_date >= start_date, NonBookableDate.start_date <= end_date),
        #                 and_(NonBookableDate.end_date >= start_date, NonBookableDate.end_date <= end_date)
        #             )
        #         )
        #     )


        # TODO: DB must calculate this
        nonbookable_count = (
            self.nonbookable_dates
                .with_entities(
                    func.sum(
                        func.abs(
                            greatest(NonBookableDate.start_date, start_date) - least(NonBookableDate.end_date, end_date)
                        ) + 1
                    )
                )
                .filter(
                    or_(
                        and_(NonBookableDate.start_date >= start_date, NonBookableDate.start_date <= end_date),
                        and_(NonBookableDate.end_date >= start_date, NonBookableDate.end_date <= end_date)
                    )
                )
                .scalar()
            ) or 0

        # nonbookable_count = 0
        # for d in nonbookable_dates_in_interval:
        #     s = max(d.start_date, start_date)
        #     e = min(d.end_date, end_date)
        #     nonbookable_count += (e-s).days + 1

        # TODO: default bookable time should go into config
        daily_time = (
            self.bookable_times
                .with_entities(
                    func.sum(
                        func.abs(
                            # extract(
                            #     'epoch',
                            #     BookableTime.start_time-BookableTime.end_time
                            # )
                            extract('epoch', BookableTime.start_time) - extract('epoch', BookableTime.end_time)
                        )
                    )
                )
                .scalar()
        ) or 3600 * 9

        return ((end_date-start_date).days + 1 - nonbookable_count) * daily_time

    def getAverageOccupation(self, start, end):
        bookable = self.getTotalBookableTime(start, end)
        booked = self.getTotalBookedTime(start, end)
        print
        print self.name
        print 'booked:', booked, 'bookable:', bookable
        return booked/float(bookable) if bookable else 0

    def getReservationStats(self):
        return utils.stats_to_dict(
            self.reservations
                .with_entities(
                    Reservation.is_live,
                    Reservation.is_cancelled,
                    Reservation.is_rejected,
                    func.count(Reservation.id)
                )
                .group_by(
                    Reservation.is_live,
                    Reservation.is_cancelled,
                    Reservation.is_rejected
                )
                .all()
        )


    @staticmethod
    def getBuildingCoordinatesByRoomIds(rids):
        return (
            Room.query
                .with_entities(
                    Room.latitude,
                    Room.longitude
                )
                .filter(
                    Room.latitude != None,
                    Room.longitude != None,
                    Room.id.in_(rids)
                )
                .first()
        )

    @staticmethod
    def getRoomsRequireVideoConferenceSetupByIds(rids):
        return (
            Room.query
                .join(Room.equipments)
                .filter(
                    RoomEquipment.name == 'Video Conference',
                    Room.id.in_(rids)
                )
                .all()
        )

    # photos

    def getLargePhotoURL(self):
        # raise NotImplementedError('todo')
        return ''

    def getSmallPhotoURL(self):
        # raise NotImplementedError('todo')
        return ''

    def saveLargePhoto(self, photo_path):
        raise NotImplementedError('todo')

    def saveSmallPhoto(self, photo_path):
        raise NotImplementedError('todo')

    def collides(self, start, end):
        return (
            self.reservations
                .join(ReservationOccurrence)
                .filter(
                    exists().where(
                        func.not_(
                            or_(
                                ReservationOccurrence.start >= end,
                                ReservationOccurrence.end <= start,
                            )
                        ),
                        ReservationOccurrence.is_cancelled == False
                    )
                )
                .scalar()
        )

    def getCollisions(self, start, end):
        return (
            self.reservations
                .join(ReservationOccurrence)
                .filter(
                    func.not_(
                        or_(
                            ReservationOccurrence.start >= end,
                            ReservationOccurrence.end <= start,
                        )
                    ),
                    ReservationOccurrence.is_cancelled == False
                )
                .all()
        )

    def getOccurrences(self, start, end, is_cancelled=False):
        return (
            self.reservations
                .join(ReservationOccurrence)
                .filter(
                    not_(
                        or_(
                            ReservationOccurrence.start >= end,
                            ReservationOccurrence.end <= start,
                        )
                    ),
                    ReservationOccurrence.is_cancelled == is_cancelled
                )
                .all()
        )
