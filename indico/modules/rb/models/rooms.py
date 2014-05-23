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
from sqlalchemy import and_, func, exists, extract, or_, type_coerce
from sqlalchemy.dialects.postgresql.base import ARRAY as sa_array
from sqlalchemy.ext.hybrid import hybrid_property
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
from indico.modules.rb.models import utils
from indico.modules.rb.models.blockings import Blocking
from indico.modules.rb.models.blocked_rooms import BlockedRoom
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.room_attributes import RoomAttribute, RoomAttributeAssociation
from indico.modules.rb.models.room_bookable_times import BookableTime
from indico.modules.rb.models.room_equipments import RoomEquipment, RoomEquipmentAssociation
from indico.modules.rb.models.room_nonbookable_dates import NonBookableDate
from indico.util.i18n import _
from indico.util.string import return_ascii, natural_sort_key
from .utils import Serializer


_cache = GenericCache('Rooms')


class RoomKind(object):
    BASIC, MODERATED, PRIVATE = 'basicRoom', 'moderatedRoom', 'privateRoom'


class Room(db.Model, Serializer):
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
        'id', 'building', 'name', 'floor', 'number', 'kind', 'booking_url', 'details_url'
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

    # many to many deleter
    # @event.listens_for(scoped_session, 'after_flush')

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

    @property
    def location_name(self):
        return self.location.name

    @property
    def booking_url(self):
        if self.id is None:
            return None
        return '#'

    @property
    def details_url(self):
        if self.id is None:
            return None
        return str(UH.UHRoomBookingRoomDetails.getURL(target=self))

    @property
    def large_photo_url(self):
        if self.id is None:
            return None
        return str(UH.UHRoomPhoto.getURL(self, size='large'))

    @property
    def small_photo_url(self):
        if self.id is None:
            return None
        return str(UH.UHRoomPhoto.getURL(self, size='small'))

    @property
    def has_photo(self):
        return self.photo_id is not None

    @hybrid_property
    def is_public(self):
        return self.is_reservable and not self.has_booking_groups

    @is_public.expression
    def is_public(self):
        return self.query \
                   .outerjoin(RoomAttributeAssociation) \
                   .outerjoin(RoomAttribute) \
                   .filter(RoomAttribute.name == 'allowed-booking-group', Room.is_reservable) \
                   .count() == 0

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
                      _('public'))[self.is_public])
        infos.append((_('needs confirmation'),
                      _('auto-confirmation'))[self.is_auto_confirm])
        if self.needs_video_conference_setup:
            infos.append(_('video conference'))

        return ', '.join(infos)

    def getEquipmentByName(self, equipment_name):
        return self.equipments \
                   .filter_by(name=func.lower(equipment_name)) \
                   .first()

    def has_equipment(self, equipment_name):
        return self.getEquipmentByName(equipment_name) is not None

    @property
    def needs_video_conference_setup(self):
        return self.has_equipment('video conference')

    @property
    def has_webcast_recording(self):
        return self.has_equipment('webcast/recording')

    @property
    def has_projector(self):
        return self.has_equipment('computer projector')

    @property
    def available_video_conference(self):
        return self.find_available_video_conference().all()

    def find_available_video_conference(self):
        vc_equipment = self.equipments \
                           .correlate(Room) \
                           .with_entities(RoomEquipment.id) \
                           .filter_by(name='video conference') \
                           .as_scalar()
        return self.equipments.filter(RoomEquipment.parent_id == vc_equipment)

    def getAttributeByName(self, attribute_name):
        return self.attributes \
                   .join(RoomAttribute) \
                   .filter(RoomAttribute.name == attribute_name) \
                   .first()

    def has_attribute(self, attribute_name):
        return self.getAttributeByName(attribute_name) is not None

    @property
    def has_booking_groups(self):
        return self.has_attribute('allowed-booking-group')

    @property
    def kind(self):
        if not self.is_reservable or self.has_booking_groups:
            return 'privateRoom'
        elif self.is_reservable and self.reservations_need_confirmation:
            return 'moderatedRoom'
        elif self.is_reservable:
            return 'basicRoom'

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

    @property
    def has_special_name(self):
        return self.name != self.generateName()

    def getFullName(self):
        if self.has_special_name:
            return u'{} - {}'.format(self.generateName(), self.name)
        else:
            return u'{}'.format(self.generateName())

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
        if kwargs:
            raise ValueError('Unexpected kwargs: {}'.format(kwargs))

        query = Room.query
        entities = [Room]

        if 'equipment' in args:
            entities.append(static_array.array_agg(RoomEquipment.name))
            query = query.\
                outerjoin(RoomEquipmentAssociation).\
                outerjoin(RoomEquipment)

        if not entities:
            raise ValueError('No data provided')

        query = query.with_entities(*entities) \
                     .outerjoin(Location, Location.id == Room.location_id) \
                     .group_by(Location.name, Room.id) \
                     .order_by(Location.name, Room.building, Room.floor, Room.number, Room.name)

        if only_active:
            query = query.filter(Room.is_active == True)

        for r in query.all():
            res = {'room': r[0]}
            for i, arg in enumerate(args):
                res[arg] = r[i + 1]
            yield res

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

    # TODO: capacity check should go into config, current 20%
    @staticmethod
    def getRoomsForRoomList(f, avatar):
        from .locations import Location

        equipment_count = len(f.equipments.data)
        equipment_subquery = db.session.query(RoomEquipmentAssociation) \
                               .with_entities(func.count(RoomEquipmentAssociation.c.room_id)) \
                               .filter(
                                    RoomEquipmentAssociation.c.room_id == Room.id,
                                    RoomEquipmentAssociation.c.equipment_id.in_(f.equipments.data)
                               ) \
                               .correlate(Room) \
                               .as_scalar()

        q = Room.query \
                .join(Location.rooms) \
                .filter(
                    Location.id == f.location_id.data if f.location_id.data else True,
                    (Room.capacity >= (f.capacity.data * 0.8)) if f.capacity.data else True,
                    Room.is_public == f.is_public.data if f.is_public.data else True,
                    Room.is_auto_confirm == f.is_auto_confirm.data if f.is_auto_confirm.data else True,
                    Room.is_active == f.is_active.data if f.is_active.data else True,
                    Room.owner_id == avatar.getId() if f.is_only_my_rooms.data else True,
                    (equipment_subquery == equipment_count) if equipment_count else True
                )

        free_search_columns = (
            'name', 'site', 'division', 'building', 'floor',
            'number', 'telephone', 'key_location', 'comments'
        )
        if f.free_search.data:
            q = q.filter(
                or_(
                    *[getattr(Room, c).ilike(u'%{}%'.format(f.free_search.data))
                      for c in free_search_columns]
                )
            )

        q = q.order_by(Room.capacity)
        return q.all()

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

    def doesHaveLiveReservations(self):
        return self.reservations.filter_by(
            is_live=True,
            is_cancelled=False,
            is_rejected=False
        ).count() > 0

    def getLiveReservations(self):
        return Reservation.find_all(
            Reservation.room == self,
            Reservation.is_live,
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

    @utils.filtered
    def filterEquipments(self, **filters):
        return RoomEquipment, self.equipments

    def getEquipmentNames(self):
        return self.equipment_names

    def getEquipmentIds(self):
        return self.equipments.with_entities(RoomEquipment.id).all()

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

    def getBlockedRoom(self, d):
        return self.blocked_rooms \
                   .join(BlockedRoom.blocking) \
                   .filter(
                       Blocking.is_active_at(d),
                       BlockedRoom.state == BlockedRoom.State.accepted
                   ) \
                   .first()

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

        if (not ignore_admin and avatar.isRBAdmin()) or (self.isOwnedBy(avatar) and self.is_active):
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

    def can_be_prebooked(self, avatar, ignore_admin=False):
        """
        Reservable rooms can be pre-booked by anyone.
        Other rooms - only by their responsibles.
        """
        return self._can_be_booked(avatar, prebook=True, ignore_admin=ignore_admin)

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
        if not self.owner_id:
            return None
        if self.owner_id == avatar.id:
            return True
        manager_groups = self.getAttributeByName('manager-group')
        if not manager_groups:
            return False
        return manager_groups.contains(avatar)

    def getGroups(self, group_name):
        groups = GroupHolder().match({'name': group_name}, exact=True, searchInAuthenticators=False)
        if groups:
            return groups
        return GroupHolder().match({'name': group_name}, exact=True)

    def getAllManagers(self):
        managers = {self.owner_id}
        manager_groups = self.get_attribute_value('manager-group')
        for group_name in (manager_groups and manager_groups['is_equipped']):
            groups = self.getGroups(group_name)
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
                        (NonBookableDate.start_date >= start_date) & (NonBookableDate.start_date <= end_date),
                        (NonBookableDate.end_date >= start_date) & (NonBookableDate.end_date <= end_date)
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
        return booked / float(bookable) if bookable else 0

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
                           ReservationOccurrence.is_cancelled == False
                       )
                   ) \
                   .scalar()

    def getCollisions(self, start, end):
        return self.reservations \
                   .join(ReservationOccurrence) \
                   .filter(
                       ~((ReservationOccurrence.start >= end) | (ReservationOccurrence.end <= start)),
                       ReservationOccurrence.is_cancelled == False
                   ) \
                   .all()

    def getOccurrences(self, start, end, is_cancelled=False):
        return self.reservations \
                   .join(ReservationOccurrence) \
                   .filter(
                       ~((ReservationOccurrence.start >= end) | (ReservationOccurrence.end <= start)),
                       ReservationOccurrence.is_cancelled == is_cancelled
                   ) \
                   .all()
