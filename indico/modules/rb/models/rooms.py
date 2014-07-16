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

import ast
import json
from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from sqlalchemy import and_, func, exists, extract, or_, type_coerce
from sqlalchemy.dialects.postgresql.base import ARRAY as sa_array
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import cast, literal
from sqlalchemy.types import Date as sa_date, Time as sa_time

from MaKaC.webinterface import urlHandlers as UH
from MaKaC.accessControl import AccessWrapper
from MaKaC.common.Locators import Locator
from MaKaC.common.cache import GenericCache
from MaKaC.errors import MaKaCError
from MaKaC.user import Avatar, AvatarHolder, GroupHolder
from indico.core.db.sqlalchemy import db
from indico.core.db.sqlalchemy.custom import greatest, least, static_array
from indico.core.errors import IndicoError
from indico.modules.rb.models import utils
from indico.modules.rb.models.blockings import Blocking
from indico.modules.rb.models.blocked_rooms import BlockedRoom
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import Reservation, RepeatMapping
from indico.modules.rb.models.room_attributes import RoomAttribute, RoomAttributeAssociation
from indico.modules.rb.models.room_bookable_times import BookableTime
from indico.modules.rb.models.room_equipments import RoomEquipment, RoomEquipmentAssociation
from indico.modules.rb.models.room_nonbookable_dates import NonBookableDate
from indico.modules.rb.models.utils import Serializer, cached, versioned_cache, db_dates_overlap
from indico.util.i18n import _
from indico.util.string import return_ascii, natural_sort_key
from indico.web.flask.util import url_for


_cache = GenericCache('Rooms')


class RoomKind(object):
    BASIC, MODERATED, PRIVATE = 'basicRoom', 'moderatedRoom', 'privateRoom'


class Room(versioned_cache(_cache, 'id'), db.Model, Serializer):
    __tablename__ = 'rooms'
    __public__ = [
        'id', 'name', 'location_name', 'floor', 'number', 'building',
        'booking_url', 'capacity', 'comments', 'owner_id', 'details_url',
        'large_photo_url', 'small_photo_url', 'has_photo', 'is_active',
        'is_reservable', 'is_auto_confirm', 'marker_description', 'kind'
    ]

    __public_exhaustive__ = __public__ + [
        'has_webcast_recording', 'needs_video_conference_setup', 'has_projector', 'is_public', 'has_booking_groups'
    ]

    __calendar_public__ = [
        'id', 'building', 'name', 'floor', 'number', 'kind', 'booking_url', 'details_url', 'location_name'
    ]

    __api_public__ = (
        'id', 'building', 'name', 'floor', 'longitude', 'latitude', ('number', 'roomNr'), ('location_name', 'location'),
        ('full_name', 'fullName'), ('booking_url', 'bookingUrl')
    )

    __api_minimal_public__ = (
        'id', ('full_name', 'fullName')
    )

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
    photo_id = db.Column(
        db.Integer,
        db.ForeignKey('photos.id')
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
        default=True,
        index=True
    )
    is_reservable = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    max_advance_days = db.Column(
        db.Integer
    )

    # relationships

    attributes = db.relationship(
        'RoomAttributeAssociation',
        backref='room',
        cascade='all, delete-orphan',
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
        backref='room',
        order_by=BookableTime.start_time,
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

    photo = db.relationship(
        'Photo',
        backref='room',
        cascade='all, delete-orphan',
        single_parent=True,
        lazy=True
    )

    reservations = db.relationship(
        'Reservation',
        backref='room',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    @hybrid_property
    def is_auto_confirm(self):
        return not self.reservations_need_confirmation

    @is_auto_confirm.expression
    def is_auto_confirm(self):
        return ~self.reservations_need_confirmation

    @property
    @cached(_cache)
    def available_video_conference(self):
        return self.find_available_video_conference().all()

    @property
    def bookable_time_per_day(self):
        bookable_time = (self.bookable_times
                             .with_entities(func.sum(BookableTime.end_time - BookableTime.start_time))
                             .group_by(BookableTime.start_time)).scalar()
        return bookable_time.total_seconds() if bookable_time else 3600 * 24  # seconds in a day

    @property
    def booking_url(self):
        if self.id is None:
            return None
        return url_for('rooms.room_book', self)

    @property
    def details_url(self):
        if self.id is None:
            return None
        return str(UH.UHRoomBookingRoomDetails.getURL(target=self))

    @property
    def full_name(self):
        if self.has_special_name:
            return u'{} - {}'.format(self.generateName(), self.name)
        else:
            return u'{}'.format(self.generateName())

    @property
    @cached(_cache)
    def has_booking_groups(self):
        return self.has_attribute('allowed-booking-group')

    @property
    @cached(_cache)
    def has_projector(self):
        return self.has_equipment('Computer Projector')

    @property
    def has_special_name(self):
        return self.name != self.generateName()

    @property
    @cached(_cache)
    def has_webcast_recording(self):
        return self.has_equipment('Webcast/Recording')

    @property
    @cached(_cache)
    def is_public(self):
        return self.is_reservable and not self.has_booking_groups

    @property
    def kind(self):
        if not self.is_reservable or self.has_booking_groups:
            return 'privateRoom'
        elif self.is_reservable and self.reservations_need_confirmation:
            return 'moderatedRoom'
        elif self.is_reservable:
            return 'basicRoom'

    @property
    def location_name(self):
        return self.location.name

    @property
    def marker_description(self):
        infos = []

        infos.append('{capacity} {label}'.format(
            capacity=self.capacity,
            label=(_('person'), _('people'))[self.capacity > 1 or self.capacity == 0]
        ))
        infos.append((_('private'),
                      _('public'))[self.is_public])
        infos.append((_('needs confirmation'),
                      _('auto-confirmation'))[self.is_auto_confirm])
        if self.needs_video_conference_setup:
            infos.append(_('video conference'))

        return ', '.join(map(unicode, infos))

    @property
    @cached(_cache)
    def needs_video_conference_setup(self):
        return self.has_equipment('Video conference')

    @property
    def large_photo_url(self):
        if self.id is None:
            return None
        return url_for('rooms.photo', self, size='large')

    @property
    def small_photo_url(self):
        if self.id is None:
            return None
        return url_for('rooms.photo', self, size='small')

    @property
    def has_photo(self):
        return self.photo_id is not None

    # core

    def __cmp__(self, other):
        if not self or not other:
            return cmp(1 if self else None, 1 if other else None)
        if self.id == other.id:
            return 0
        return (cmp(self.location.name, other.location.name) or
                cmp(self.building, other.building) or
                cmp(self.floor, other.floor) or
                cmp(self.number, other.number) or
                cmp(self.name, other.name))

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    @return_ascii
    def __repr__(self):
        return u'<Room({0}, {1}, {2})>'.format(
            self.id,
            self.location_id,
            self.name
        )

    def has_equipment(self, equipment_name):
        return self.equipments.filter_by(name=equipment_name).count() > 0

    def find_available_video_conference(self):
        vc_equipment = self.equipments \
                           .correlate(Room) \
                           .with_entities(RoomEquipment.id) \
                           .filter_by(name='Video conference') \
                           .as_scalar()
        return self.equipments.filter(RoomEquipment.parent_id == vc_equipment)

    def getAttributeByName(self, attribute_name):
        return self.attributes \
                   .join(RoomAttribute) \
                   .filter(RoomAttribute.name == attribute_name) \
                   .first()

    def has_attribute(self, attribute_name):
        return self.getAttributeByName(attribute_name) is not None

    def getLocator(self):
        locator = Locator()
        locator['roomLocation'] = self.location.name
        locator['roomID'] = self.id
        return locator

    def generateName(self):
        return u'{}-{}-{}'.format(
            self.building,
            self.floor,
            self.number
        )

    def getFullName(self):
        return self.full_name

    def updateName(self):
        if not self.name and self.building and self.floor and self.number:
            self.name = self.generateName()

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

    @classmethod
    def find_all(cls, *args, **kwargs):
        """
        Sorts by location and full name.
        """
        # TODO: not complete yet
        rooms = super(Room, cls).find_all(*args, **kwargs)
        rooms.sort(key=lambda x: natural_sort_key(x.location.name + x.getFullName()))
        return rooms

    @staticmethod
    def getRoomsWithData(*args, **kwargs):
        from .locations import Location

        only_active = kwargs.pop('only_active', True)
        filters = kwargs.pop('filters', None)
        order = kwargs.pop('order', [Location.name, Room.building, Room.floor, Room.number, Room.name])
        if kwargs:
            raise ValueError('Unexpected kwargs: {}'.format(kwargs))

        query = Room.query
        entities = [Room]

        if 'equipment' in args:
            entities.append(static_array.array_agg(RoomEquipment.name))
            query = query.outerjoin(RoomEquipmentAssociation).outerjoin(RoomEquipment)
        if 'vc_equipment' in args or 'non_vc_equipment' in args:
            vc_id_subquery = db.session.query(RoomEquipment.id) \
                                       .correlate(Room) \
                                       .filter_by(name='Video conference') \
                                       .join(RoomEquipmentAssociation) \
                                       .filter(RoomEquipmentAssociation.c.room_id == Room.id) \
                                       .as_scalar()

            if 'vc_equipment' in args:
                # noinspection PyTypeChecker
                entities.append(static_array.array(
                    db.session.query(RoomEquipment.name)
                    .join(RoomEquipmentAssociation)
                    .filter(
                        RoomEquipmentAssociation.c.room_id == Room.id,
                        RoomEquipment.parent_id == vc_id_subquery
                    )
                    .order_by(RoomEquipment.name)
                    .as_scalar()
                ))
            if 'non_vc_equipment' in args:
                # noinspection PyTypeChecker
                entities.append(static_array.array(
                    db.session.query(RoomEquipment.name)
                    .join(RoomEquipmentAssociation)
                    .filter(
                        RoomEquipmentAssociation.c.room_id == Room.id,
                        (RoomEquipment.parent_id == None) | (RoomEquipment.parent_id != vc_id_subquery)
                    )
                    .order_by(RoomEquipment.name)
                    .as_scalar()
                ))

        if not entities:
            raise ValueError('No data provided')

        query = query.with_entities(*entities) \
                     .outerjoin(Location, Location.id == Room.location_id) \
                     .group_by(Location.name, Room.id)

        if only_active:
            query = query.filter(Room.is_active)
        if filters:
            query = query.filter(*filters)
        if order:
            query = query.order_by(*order)

        keys = ('room',) + tuple(args)
        return (dict(zip(keys, row if args else [row])) for row in query)

    @staticmethod
    def getMaxCapacity():
        key = 'maxcapacity'
        max_capacity = _cache.get(key)
        if max_capacity is None:
            records = Room.query \
                          .with_entities(func.max(Room.capacity).label('capacity')) \
                          .all()
            max_capacity = records[0].capacity
            _cache.set(key, max_capacity, 300)
        return max_capacity

    @staticmethod
    def getRoomsByName(name):
        return Room.find_all(name=name)

    @staticmethod
    def getRoomByName(name):
        return Room.query.filter_by(name=name).first()

    @staticmethod
    def filter_available(start_dt, end_dt, repetition, include_pre_bookings=True, include_pending_blockings=True):
        """Returns a SQLAlchemy filter criterion ensuring that the room is available during the given time."""
        # Check availability against reservation occurrences
        dummy_occurrences = ReservationOccurrence.create_series(start_dt, end_dt, repetition)
        overlap_criteria = ReservationOccurrence.filter_overlap(dummy_occurrences)
        reservation_criteria = [Reservation.room_id == Room.id,
                                ReservationOccurrence.is_valid,
                                or_(*overlap_criteria)]
        if not include_pre_bookings:
            reservation_criteria.append(Reservation.is_confirmed)
        occurrences_filter = Reservation.occurrences.any(and_(*reservation_criteria))
        # Check availability against blockings
        if include_pending_blockings:
            valid_states = (BlockedRoom.State.accepted, BlockedRoom.State.pending)
        else:
            valid_states = (BlockedRoom.State.accepted,)
        blocking_criteria = [Blocking.id == BlockedRoom.blocking_id,
                             Blocking.start_date <= start_dt,
                             Blocking.end_date >= end_dt,
                             BlockedRoom.state.in_(valid_states)]
        blockings_filter = Room.blocked_rooms.any(and_(*blocking_criteria))
        return ~occurrences_filter & ~blockings_filter

    @staticmethod
    def getRoomsForRoomList(form, avatar):
        from .locations import Location

        equipment_count = len(form.equipments.data)
        equipment_subquery = (
            db.session.query(RoomEquipmentAssociation)
            .with_entities(func.count(RoomEquipmentAssociation.c.room_id))
            .filter(
                RoomEquipmentAssociation.c.room_id == Room.id,
                RoomEquipmentAssociation.c.equipment_id.in_(eq.id for eq in form.equipments.data)
            )
            .correlate(Room)
            .as_scalar()
        )

        q = (
            Room.query
            .join(Location.rooms)
            .filter(
                Location.id == form.location.data.id if form.location.data else True,
                (Room.capacity >= (form.capacity.data * 0.8)) if form.capacity.data else True,
                Room.is_reservable if form.is_only_public.data else True,
                Room.is_auto_confirm if form.is_auto_confirm.data else True,
                Room.is_active if form.is_only_active.data or not form.is_only_active else True,
                Room.owner_id == avatar.getId() if form.is_only_my_rooms.data else True,
                (equipment_subquery == equipment_count) if equipment_count else True)
        )

        if form.available.data != -1:
            repetition = RepeatMapping.getNewMapping(ast.literal_eval(form.repeatability.data))
            is_available = Room.filter_available(form.start_date.data, form.end_date.data, repetition,
                                                 include_pre_bookings=form.include_pre_bookings.data,
                                                 include_pending_blockings=form.include_pending_blockings.data)
            # Filter the search results
            if form.available.data == 0:  # booked/unavailable
                q = q.filter(~is_available)
            elif form.available.data == 1:  # available
                q = q.filter(is_available)

        free_search_columns = (
            'name', 'site', 'division', 'building', 'floor', 'number', 'telephone', 'key_location', 'comments'
        )
        if form.details.data:
            # Attributes are stored JSON-encoded, so we need to JSON-encode the provided string and remove the quotes
            # afterwards since PostgreSQL currently does not expose a function to decode a JSON string:
            # http://www.postgresql.org/message-id/51FBF787.5000408@dunslane.net
            details = form.details.data.lower()
            details_str = u'%{}%'.format(details)
            details_json = u'%{}%'.format(json.dumps(details)[1:-1])
            free_search_criteria = [getattr(Room, c).ilike(details_str) for c in free_search_columns]
            free_search_criteria.append(Room.attributes.any(RoomAttributeAssociation.raw_data.ilike(details_json)))
            q = q.filter(or_(*free_search_criteria))

        q = q.order_by(Room.capacity)
        rooms = q.all()
        # Apply a bunch of filters which are *much* easier to do here than in SQL!
        if form.is_only_public.data:
            # This may trigger additional SQL queries but is_public is cached and doing this check here is *much* easier
            rooms = [r for r in rooms if r.is_public]
        if form.capacity.data:
            # Unless it would result in an empty resultset we don't want to show room which >20% more capacity
            # than requested. This cannot be done easily in SQL so we do that logic here after the SQL query already
            # weeded out rooms that are too small
            matching_capacity_rooms = [r for r in rooms if r.capacity <= form.capacity.data * 1.2]
            if matching_capacity_rooms:
                rooms = matching_capacity_rooms
        return rooms

    def getResponsible(self):
        return AvatarHolder().getById(self.owner_id)

    def getResponsibleName(self):
        r = self.getResponsible()
        if r:
            return r.getFullName()

    # reservations

    def doesHaveLiveReservations(self):
        return self.reservations.filter_by(
            is_archived=False,
            is_cancelled=False,
            is_rejected=False
        ).count() > 0

    def getLiveReservations(self):
        return Reservation.find_all(
            Reservation.room == self,
            ~Reservation.is_archived,
            ~Reservation.is_cancelled,
            ~Reservation.is_rejected
        )

    def removeReservations(self):
        del self.reservations[:]

    @staticmethod
    def isAvatarResponsibleForRooms(avatar):
        return Room.query.filter_by(owner_id=avatar.id).count() > 0

    def getLocationName(self):
        return self.location.name

    @staticmethod
    def getReservationsForAvailability(start_date, end_date, room_id_list):
        from .locations import Location

        date_query = db.session.query(
            cast(func.generate_series(start_date.date(), end_date.date(), timedelta(1)),
                 sa_date).label('available_date')
        ).subquery()

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

        return db.session \
                 .query() \
                 .select_from(date_query) \
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
                 ) \
                 .outerjoin(
                     Location,
                     literal(1) == 1  # cartesian product
                 ) \
                 .outerjoin(
                     Room,
                     Location.rooms
                 ) \
                 .outerjoin(
                     Reservation,
                     Room.reservations
                 ) \
                 .outerjoin(
                     ReservationOccurrence,
                     and_(
                         Reservation.occurrences,
                         date_query.c.available_date == cast(ReservationOccurrence.start, sa_date)
                     )
                 ) \
                 .outerjoin(
                     BlockedRoom,
                     BlockedRoom.room_id == Room.id
                 ) \
                 .outerjoin(
                     Blocking,
                     Blocking.id == BlockedRoom.blocking_id
                 ) \
                 .correlate(date_query) \
                 .filter(
                     Room.id.in_(room_id_list),
                 ) \
                 .group_by(date_query.c.available_date, Room.id) \
                 .order_by(date_query.c.available_date, Room.name) \
                 .all()

    @staticmethod
    def getReservationsForAvailability2(start_date, end_date, room_id_list):
        date_query = db.session.query(
            cast(func.generate_series(start_date.date(), end_date.date(), timedelta(1)),
                 sa_date).label('available_date')
        ).subquery()

        return db.session \
                 .query(date_query.c.available_date) \
                 .select_from(date_query) \
                 .correlate(date_query) \
                 .filter(date_query.c.available_date != date(2014, 2, 18)) \
                 .all()

    # equipments

    def getEquipmentNames(self):
        return self.equipment_names

    def getEquipmentIds(self):
        return self.equipments.with_entities(RoomEquipment.id).all()

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
        return all(map(has, names))

    def needsVideoConferenceSetup(self):
        return self.hasEquipment('Video Conference')

    def hasWebcastRecording(self):
        return self.hasEquipment('Webcast/Recording')

    def getVerboseEquipment(self):
        return self.equipments \
                   .with_entities(func.array_to_string(func.array_agg(RoomEquipment.name), ', ')) \
                   .scalar()
        # return (self.equipments
        #         .with_entities(func.group_concat(RoomEquipment.name))
        #         .scalar())

    def isCloseToBuilding(self):
        raise NotImplementedError('todo')

    def belongsTo(self, avatar):
        raise NotImplementedError('todo')

    # blocked rooms

    def get_blocked_rooms(self, *dates, **kwargs):
        states = kwargs.get('states', (BlockedRoom.State.accepted,))
        return (self.blocked_rooms
                .options(joinedload(BlockedRoom.blocking))
                .join(BlockedRoom.blocking)
                .filter(or_(Blocking.is_active_at(d) for d in dates),
                        BlockedRoom.state.in_(states))
                .all())

    # attributes

    # def getAttributeByName(self, name):
    #     attribute = (self.attributes
    #                      .with_entities(RoomAttribute)
    #                      .join(RoomAttribute.key)
    #                      .filter(AttributeKey.name == name)
    #                      .first())
    #     return attribute

    def get_attribute_value(self, name):
        attr = self.getAttributeByName(name)
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
        return self.equipments \
                   .join(Room.attributes) \
                   .filter(
                       exists().where(
                           or_(
                               RoomEquipment.name.ilike(like_query_param),
                               RoomAttribute.raw_data.ilike(like_query_param)
                           )
                       )
                   ) \
                   .scalar()

    # TODO: 20% should go to config
    def isGoodCapacity(self, capacity):
        if not self.capacity or self.capacity == 0:
            return False
        return abs(self.capacity - capacity) / float(self.capacity) <= 0.2

    # access checks

    def hasAllowedBookingGroups(self):
        return False
        # return self.getAttributeByName('allowed-booking-group') is not None

    def canBeViewedBy(self, accessWrapper):
        """Room details are public - anyone can view."""
        return True

    @utils.accessChecked
    def _can_be_booked(self, avatar, prebook=False, ignore_admin=False):
        if not avatar:
            return False

        if (not ignore_admin and avatar.isRBAdmin()) or (self.is_owned_by(avatar) and self.is_active):
            return True

        if self.is_active and self.is_reservable and (prebook or not self.reservations_need_confirmation):
            group_name = self.get_attribute_value('allowed-booking-group')
            if not group_name or avatar.is_member_of_group(group_name):
                return True

        return False

    def can_be_booked(self, avatar, ignore_admin=False):
        """
        Reservable rooms which does not require pre-booking can be booked by anyone.
        Other rooms - only by their responsibles.
        """
        return self._can_be_booked(avatar, ignore_admin=ignore_admin)

    def can_be_overriden(self, avatar):
        return avatar.isRBAdmin() or self.is_owned_by(avatar)

    def can_be_prebooked(self, avatar, ignore_admin=False):
        """
        Reservable rooms can be pre-booked by anyone.
        Other rooms - only by their responsibles.
        """
        return self._can_be_booked(avatar, prebook=True, ignore_admin=ignore_admin)

    def can_be_modified(self, accessWrapper):
        """Only admin can modify rooms."""
        if not accessWrapper:
            return False

        if isinstance(accessWrapper, AccessWrapper):
            avatar = accessWrapper.getUser()
            return avatar.isRBAdmin() if avatar else False
        elif isinstance(accessWrapper, Avatar):
            return accessWrapper.isRBAdmin()

        raise MaKaCError(_('canModify requires either AccessWrapper or Avatar object'))

    def can_be_deleted(self, accessWrapper):
        return self.can_be_modified(accessWrapper)

    def is_owned_by(self, avatar):
        """
        Returns True if user is responsible for this room. False otherwise.
        """
        # legacy check, currently every room must be owned by someone
        if not self.owner_id:
            return None

        if self.owner_id == avatar.id:
            return True
        manager_group = self.get_attribute_value('manager-group')
        if not manager_group:
            return False
        return avatar.is_member_of_group(manager_group)

    def getGroups(self, group_name):
        groups = GroupHolder().match({'name': group_name}, exact=True, searchInAuthenticators=False)
        if groups:
            return groups
        return GroupHolder().match({'name': group_name}, exact=True)

    def getAllManagers(self):
        managers = {self.owner_id}
        manager_group = self.get_attribute_value('manager-group')
        groups = self.getGroups(manager_group) if manager_group else None
        if groups and len(groups) == 1:
            managers |= set(groups[0].getMemberList())
        return managers

    def checkManagerGroupExistence(self):
        attribute = self.getAttributeByName('manager-group')
        if attribute:
            for group_name in attribute.value.get('is_equipped', []):
                if not self.getGroups(group_name):
                    attribute.value['is_equipped'] = ['Error: unknown mailing list']
                    break

    def hasManagerGroup(self):
        attribute = self.getAttributeByName('manager-group')
        return attribute and attribute.value.get('is_equipped', [])

    def notifyAboutResponsibility(self):
        """
        Notifies (e-mails) previous and new responsible about
        responsibility change. Called after creating/updating the room.
        """
        pass

    @staticmethod
    def getBuildingCoordinatesByRoomIds(rids):
        return Room.query \
                   .with_entities(
                       Room.latitude,
                       Room.longitude
                   ) \
                   .filter(
                       Room.latitude != None,
                       Room.longitude != None,
                       Room.id.in_(rids)
                   ) \
                   .first()

    @staticmethod
    def getRoomsRequireVideoConferenceSetupByIds(rids):
        return Room.query \
                   .join(Room.equipments) \
                   .filter(
                       RoomEquipment.name == 'Video Conference',
                       Room.id.in_(rids)
                   ) \
                   .all()

    def collides(self, start, end):
        return self.reservations \
                   .join(ReservationOccurrence) \
                   .filter(
                       exists().where(
                           ~((ReservationOccurrence.start >= end) | (ReservationOccurrence.end <= start)),
                           ReservationOccurrence.is_valid
                       )
                   ) \
                   .scalar()

    def getCollisions(self, start, end):
        return self.reservations \
                   .join(ReservationOccurrence) \
                   .filter(
                       ~((ReservationOccurrence.start >= end) | (ReservationOccurrence.end <= start)),
                       ReservationOccurrence.is_valid
                   ) \
                   .all()

    def getOccurrences(self, start, end, is_cancelled=False):
        return self.reservations \
                   .join(ReservationOccurrence) \
                   .filter(
                       ~((ReservationOccurrence.start >= end) | (ReservationOccurrence.end <= start)),
                       ReservationOccurrence.is_valid == (not is_cancelled)
                   ) \
                   .all()

    def check_advance_days(self, end_date, user=None, quiet=False):
        if not self.max_advance_days:
            return
        if user and (user.isRBAdmin() or self.is_owned_by(user)):
            return
        advance_days = (end_date - date.today()).days
        ok = advance_days < self.max_advance_days
        if quiet:
            return ok
        elif not ok:
            msg = _('You cannot book this room more than {} days in advance')
            raise IndicoError(msg.format(self.max_advance_days))

    def check_bookable_times(self, start_time, end_time, user=None, quiet=False):
        if user and (user.isRBAdmin() or self.is_owned_by(user)):
            return True
        bookable_times = self.bookable_times.all()
        if not bookable_times:
            return True
        for bt in bookable_times:
            if bt.fits_period(start_time, end_time):
                return True
        if quiet:
            return False
        raise IndicoError('Room cannot be booked at this time')

    def get_nonbookable_days(self, start_date, end_date):
        earliest_day = greatest(NonBookableDate.start_date, start_date)
        latest_day = least(NonBookableDate.end_date, end_date)
        query = (self.nonbookable_dates.with_entities(func.sum(latest_day - earliest_day) + timedelta(1))
                 .filter(db_dates_overlap(NonBookableDate, 'start_date', start_date, 'end_date', end_date))
                 .group_by(NonBookableDate.end_date))
        return (query.scalar() or timedelta()).days
