# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

import ast
import json
import warnings
from datetime import date, time

from sqlalchemy import and_, cast, func, or_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import contains_eager, joinedload, load_only, raiseload

from indico.core.db.sqlalchemy import db
from indico.core.db.sqlalchemy.custom import static_array
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.db.sqlalchemy.protection import ProtectionManagersMixin, ProtectionMode
from indico.core.db.sqlalchemy.util.cache import cached, versioned_cache
from indico.core.db.sqlalchemy.util.queries import db_dates_overlap, escape_like
from indico.core.errors import NoReportError
from indico.legacy.common.cache import GenericCache
from indico.modules.groups import GroupProxy
from indico.modules.rb.models.blocked_rooms import BlockedRoom
from indico.modules.rb.models.blockings import Blocking
from indico.modules.rb.models.equipment import EquipmentType, RoomEquipmentAssociation
from indico.modules.rb.models.favorites import favorite_room_table
from indico.modules.rb.models.principals import RoomPrincipal
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import RepeatMapping, Reservation
from indico.modules.rb.models.room_attributes import RoomAttribute, RoomAttributeAssociation
from indico.modules.rb.models.room_bookable_hours import BookableHours
from indico.modules.rb.models.room_nonbookable_periods import NonBookablePeriod
from indico.modules.rb.util import rb_is_admin
from indico.util.decorators import classproperty
from indico.util.i18n import _
from indico.util.locators import locator_property
from indico.util.serializer import Serializer
from indico.util.string import format_repr, natural_sort_key, return_ascii
from indico.util.user import unify_user_args
from indico.web.flask.util import url_for


_cache = GenericCache('Rooms')


class Room(versioned_cache(_cache, 'id'), ProtectionManagersMixin, db.Model, Serializer):
    __tablename__ = 'rooms'
    __table_args__ = (db.UniqueConstraint('id', 'location_id'),  # useless but needed for the LocationMixin fkey
                      db.CheckConstraint("verbose_name != ''", 'verbose_name_not_empty'),
                      {'schema': 'roombooking'})

    default_protection_mode = ProtectionMode.public
    disallowed_protection_modes = frozenset({ProtectionMode.inheriting})

    __public__ = [
        'id', 'name', 'location_name', 'floor', 'number', 'building',
        'booking_url', 'capacity', 'comments', 'owner_id', 'details_url',
        'large_photo_url', 'has_photo', 'sprite_position', 'is_active',
        'is_reservable', 'is_auto_confirm', 'marker_description', 'kind',
        'booking_limit_days'
    ]

    __public_exhaustive__ = __public__ + [
        'has_webcast_recording', 'has_vc', 'has_projector', 'is_public', 'has_booking_groups'
    ]

    __calendar_public__ = [
        'id', 'building', 'name', 'floor', 'number', 'kind', 'booking_url', 'details_url', 'location_name',
        'max_advance_days'
    ]

    __api_public__ = (
        'id', 'building', 'name', 'floor', 'longitude', 'latitude', ('number', 'roomNr'), ('location_name', 'location'),
        ('full_name', 'fullName'), ('booking_url', 'bookingUrl')
    )

    __api_minimal_public__ = (
        'id', ('full_name', 'fullName')
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    location_id = db.Column(
        db.Integer,
        db.ForeignKey('roombooking.locations.id'),
        nullable=False
    )
    photo_id = db.Column(
        db.Integer,
        db.ForeignKey('roombooking.photos.id')
    )
    #: Verbose name for the room (long)
    verbose_name = db.Column(
        db.String,
        nullable=True,
        default=None
    )
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
    notification_before_days = db.Column(
        db.Integer
    )
    notification_before_days_weekly = db.Column(
        db.Integer
    )
    notification_before_days_monthly = db.Column(
        db.Integer
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
    notifications_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
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
    longitude = db.Column(
        db.Float
    )
    latitude = db.Column(
        db.Float
    )
    comments = db.Column(
        db.String
    )
    owner_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=False
    )
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
    booking_limit_days = db.Column(
        db.Integer
    )

    acl_entries = db.relationship(
        'RoomPrincipal',
        lazy=True,
        backref='room',
        cascade='all, delete-orphan',
        collection_class=set
    )

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

    bookable_hours = db.relationship(
        'BookableHours',
        backref='room',
        order_by=BookableHours.start_time,
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    available_equipment = db.relationship(
        'EquipmentType',
        secondary=RoomEquipmentAssociation,
        backref='rooms',
        lazy=True
    )

    nonbookable_periods = db.relationship(
        'NonBookablePeriod',
        backref='room',
        order_by=NonBookablePeriod.end_dt.desc(),
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

    favorite_of = db.relationship(
        'User',
        secondary=favorite_room_table,
        lazy=True,
        collection_class=set,
        backref=db.backref('favorite_rooms', lazy=True, collection_class=set),
    )

    #: The owner of the room. If the room has the `manager-group`
    #: attribute set, any users in that group are also considered
    #: owners when it comes to management privileges.
    #: Use :meth:`is_owned_by` for ownership checks that should
    #: also check against the management group.
    owner = db.relationship(
        'User',
        # subquery load since a normal joinedload breaks `get_with_data`
        lazy='subquery',
        backref=db.backref(
            'owned_rooms',
            lazy='dynamic'
        )
    )

    # relationship backrefs:
    # - breaks (Break.own_room)
    # - contributions (Contribution.own_room)
    # - events (Event.own_room)
    # - location (Location.rooms)
    # - session_blocks (SessionBlock.own_room)
    # - sessions (Session.own_room)

    @hybrid_property
    def is_auto_confirm(self):
        return not self.reservations_need_confirmation

    @is_auto_confirm.expression
    def is_auto_confirm(self):
        return ~self.reservations_need_confirmation

    @property
    def booking_url(self):
        if self.id is None:
            return None
        return url_for('rooms.room_book', self)

    @property
    def details_url(self):
        if self.id is None:
            return None
        return url_for('rooms.roomBooking-roomDetails', self)

    @property
    def large_photo_url(self):
        if self.id is None:
            return None
        return url_for('rooms.photo', roomID=self.id)

    @property
    def map_url(self):
        if self.location.map_url_template:
            return self.location.map_url_template.format(
                building=self.building,
                floor=self.floor,
                number=self.number
            )
        else:
            return None

    @property
    def has_photo(self):
        return self.photo_id is not None

    @hybrid_property
    def name(self):
        return self.generate_name()

    @name.expression
    def name(cls):
        q = (db.session.query(db.m.Location.room_name_format)
             .filter(db.m.Location.id == cls.location_id)
             .correlate(Room)
             .as_scalar())
        return db.func.format(q, cls.building, cls.floor, cls.number)

    @hybrid_property
    def full_name(self):
        if self.verbose_name:
            return u'{} - {}'.format(self.generate_name(), self.verbose_name)
        else:
            return u'{}'.format(self.generate_name())

    @full_name.expression
    def full_name(cls):
        return db.case([
            [cls.verbose_name.isnot(None), cls.name + ' - ' + cls.verbose_name]
        ], else_=cls.name)

    @property
    @cached(_cache)
    def has_booking_groups(self):
        return self.has_attribute('allowed-booking-group')

    @property
    @cached(_cache)
    def has_projector(self):
        return self.has_equipment(u'Computer Projector', u'Video projector 4:3', u'Video projector 16:9')

    @property
    @cached(_cache)
    def has_webcast_recording(self):
        return self.has_equipment('Webcast/Recording')

    @property
    @cached(_cache)
    def has_vc(self):
        return self.has_equipment('Video conference')

    @property
    def kind(self):
        if not self.is_reservable or self.has_booking_groups:
            return 'privateRoom'
        elif self.reservations_need_confirmation:
            return 'moderatedRoom'
        else:
            return 'basicRoom'

    @property
    def location_name(self):
        return self.location.name

    @property
    def marker_description(self):
        infos = []

        infos.append(u'{capacity} {label}'.format(capacity=self.capacity,
                                                  label=_(u'person') if self.capacity == 1 else _(u'people')))
        infos.append(_(u'public') if self.is_public else _(u'private'))
        infos.append(_(u'auto-confirmation') if self.is_auto_confirm else _(u'needs confirmation'))
        if self.has_vc:
            infos.append(_(u'videoconference'))

        return u', '.join(map(unicode, infos))

    @property
    def manager_emails(self):
        manager_group = self.get_attribute_value('manager-group')
        if not manager_group:
            return set()
        group = GroupProxy.get_named_default_group(manager_group)
        return {u.email for u in group.get_members()}

    @property
    def notification_emails(self):
        return set(filter(None, map(unicode.strip, self.get_attribute_value(u'notification-email', u'').split(u','))))

    @property
    def sprite_position(self):
        sprite_mapping = _cache.get('rooms-sprite-mapping')
        return sprite_mapping.get(self.id, 0) if sprite_mapping else 0  # placeholder at position 0

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'full_name')

    @cached(_cache)
    def has_equipment(self, *names):
        available = {x.name for x in self.available_equipment}
        return bool(available & set(names))

    def get_attribute_by_name(self, attribute_name):
        return (self.attributes
                .join(RoomAttribute)
                .filter(RoomAttribute.name == attribute_name)
                .first())

    def has_attribute(self, attribute_name):
        return self.get_attribute_by_name(attribute_name) is not None

    @cached(_cache)
    def get_attribute_value(self, name, default=None):
        attr = self.get_attribute_by_name(name)
        return attr.value if attr else default

    def set_attribute_value(self, name, value):
        attr = self.get_attribute_by_name(name)
        if attr:
            if value:
                attr.value = value
            else:
                self.attributes.filter(RoomAttributeAssociation.attribute_id == attr.attribute_id) \
                    .delete(synchronize_session='fetch')
        elif value:
            attr = RoomAttribute.query.filter_by(name=name).first()
            if not attr:
                raise ValueError("Attribute {} does not exist".format(name))
            attr_assoc = RoomAttributeAssociation()
            attr_assoc.value = value
            attr_assoc.attribute = attr
            self.attributes.append(attr_assoc)
        db.session.flush()

    @locator_property
    def locator(self):
        return {'roomLocation': self.location_name, 'roomID': self.id}

    def generate_name(self):
        if self.location is None:
            warnings.warn('Room has no location; using default name format')
            return '{}/{}-{}'.format(self.building, self.floor, self.number)
        return self.location.room_name_format.format(
            building=self.building,
            floor=self.floor,
            number=self.number
        )

    @classmethod
    def find_all(cls, *args, **kwargs):
        """Retrieves rooms, sorted by location and full name"""
        rooms = super(Room, cls).find_all(*args, **kwargs)
        rooms.sort(key=lambda r: natural_sort_key(r.location_name + r.full_name))
        return rooms

    @classmethod
    def find_with_attribute(cls, attribute):
        """Search rooms which have a specific attribute"""
        return (Room.query
                .with_entities(Room, RoomAttributeAssociation.value)
                .join(Room.attributes, RoomAttributeAssociation.attribute)
                .filter(RoomAttribute.name == attribute)
                .all())

    @staticmethod
    def get_with_data(*args, **kwargs):
        from indico.modules.rb.models.locations import Location

        only_active = kwargs.pop('only_active', True)
        filters = kwargs.pop('filters', None)
        order = kwargs.pop('order', [Location.name, Room.building, Room.floor, Room.number, Room.verbose_name])
        if kwargs:
            raise ValueError('Unexpected kwargs: {}'.format(kwargs))

        query = Room.query
        entities = [Room]

        if 'equipment' in args:
            entities.append(static_array.array_agg(EquipmentType.name))
            query = query.outerjoin(RoomEquipmentAssociation).outerjoin(EquipmentType)

        query = (query.with_entities(*entities)
                 .outerjoin(Location, Location.id == Room.location_id)
                 .group_by(Location.name, Room.id))

        if only_active:
            query = query.filter(Room.is_active)
        if filters:  # pragma: no cover
            query = query.filter(*filters)
        if order:  # pragma: no cover
            query = query.order_by(*order)

        keys = ('room',) + tuple(args)
        return (dict(zip(keys, row if args else [row])) for row in query)

    @classproperty
    @staticmethod
    def max_capacity():
        return db.session.query(db.func.max(Room.capacity)).scalar() or 0

    @staticmethod
    def filter_available(start_dt, end_dt, repetition, include_blockings=True, include_pre_bookings=True,
                         include_pending_blockings=False):
        """Returns a SQLAlchemy filter criterion ensuring that the room is available during the given time."""
        # Check availability against reservation occurrences
        dummy_occurrences = ReservationOccurrence.create_series(start_dt, end_dt, repetition)
        overlap_criteria = ReservationOccurrence.filter_overlap(dummy_occurrences)
        reservation_criteria = [Reservation.room_id == Room.id,
                                ReservationOccurrence.is_valid,
                                overlap_criteria]
        if not include_pre_bookings:
            reservation_criteria.append(Reservation.is_accepted)
        occurrences_filter = (Reservation.query
                              .join(ReservationOccurrence.reservation)
                              .filter(and_(*reservation_criteria)))
        # Check availability against blockings
        filters = ~occurrences_filter.exists()
        if include_blockings:
            if include_pending_blockings:
                valid_states = (BlockedRoom.State.accepted, BlockedRoom.State.pending)
            else:
                valid_states = (BlockedRoom.State.accepted,)
            # TODO: only take blockings into account which the user cannot override
            blocking_criteria = [Room.id == BlockedRoom.room_id,
                                 BlockedRoom.state.in_(valid_states),
                                 db_dates_overlap(Blocking, 'start_date', end_dt.date(), 'end_date', start_dt.date(),
                                                  inclusive=True)]
            blockings_filter = (BlockedRoom.query
                                .join(Blocking.blocked_rooms)
                                .filter(and_(*blocking_criteria)))
            return filters & ~blockings_filter.exists()
        return filters

    @staticmethod
    def filter_bookable_hours(start_time, end_time):
        if end_time == time(0):
            end_time = time(23, 59, 59)
        period_end_time = db.case({time(0): time(23, 59, 59)}, else_=BookableHours.end_time,
                                  value=BookableHours.end_time)
        bookable_hours_filter = Room.bookable_hours.any(
            (BookableHours.start_time <= start_time) & (period_end_time >= end_time)
        )
        return ~Room.bookable_hours.any() | bookable_hours_filter

    @staticmethod
    def filter_nonbookable_periods(start_dt, end_dt):
        return ~Room.nonbookable_periods.any(and_(NonBookablePeriod.start_dt <= end_dt,
                                                  NonBookablePeriod.end_dt >= start_dt))

    @staticmethod
    def find_with_filters(filters, user=None):
        from indico.modules.rb.models.locations import Location

        equipment_count = len(filters.get('available_equipment', ()))
        equipment_subquery = None
        if equipment_count:
            equipment_subquery = (
                db.session.query(RoomEquipmentAssociation)
                .with_entities(func.count(RoomEquipmentAssociation.c.room_id))
                .filter(
                    RoomEquipmentAssociation.c.room_id == Room.id,
                    RoomEquipmentAssociation.c.equipment_id.in_(eq.id for eq in filters['available_equipment'])
                )
                .correlate(Room)
                .as_scalar()
            )

        capacity = filters.get('capacity')
        q = (
            Room.query
            .join(Location.rooms)
            .filter(
                Location.id == filters['location'].id if filters.get('location') else True,
                ((Room.capacity >= (capacity * 0.8)) | (Room.capacity == None)) if capacity else True,
                Room.is_reservable if filters.get('is_only_public') else True,
                Room.is_auto_confirm if filters.get('is_auto_confirm') else True,
                Room.is_active if filters.get('is_only_active', False) else True,
                (equipment_subquery == equipment_count) if equipment_subquery is not None else True)
        )

        if filters.get('available', -1) != -1:
            repetition = RepeatMapping.convert_legacy_repeatability(ast.literal_eval(filters['repeatability']))
            is_available = Room.filter_available(filters['start_dt'], filters['end_dt'], repetition,
                                                 include_blockings=True,
                                                 include_pre_bookings=filters.get('include_pre_bookings', True),
                                                 include_pending_blockings=filters.get('include_pending_blockings',
                                                                                       True))
            # Filter the search results
            if filters['available'] == 0:  # booked/unavailable
                q = q.filter(~is_available)
            elif filters['available'] == 1:  # available
                q = q.filter(is_available)
            else:
                raise ValueError('Unexpected availability value')

        free_search_columns = (
            'full_name', 'site', 'division', 'building', 'floor', 'number', 'telephone', 'key_location', 'comments'
        )
        if filters.get('details'):
            # Attributes are stored JSON-encoded, so we need to JSON-encode the provided string and remove the quotes
            # afterwards since PostgreSQL currently does not expose a function to decode a JSON string:
            # http://www.postgresql.org/message-id/51FBF787.5000408@dunslane.net
            details = filters['details'].lower()
            details_str = u'%{}%'.format(escape_like(details))
            details_json = u'%{}%'.format(escape_like(json.dumps(details)[1:-1]))
            free_search_criteria = [getattr(Room, c).ilike(details_str) for c in free_search_columns]
            free_search_criteria.append(Room.attributes.any(cast(RoomAttributeAssociation.value, db.String)
                                                            .ilike(details_json)))
            q = q.filter(or_(*free_search_criteria))

        q = q.order_by(Room.capacity)
        rooms = q.all()
        # Apply a bunch of filters which are *much* easier to do here than in SQL!
        if filters.get('is_only_public'):
            # This may trigger additional SQL queries but is_public is cached and doing this check here is *much* easier
            rooms = [r for r in rooms if r.is_public]
        if filters.get('is_only_my_rooms'):
            assert user is not None
            rooms = [r for r in rooms if r.is_owned_by(user)]
        if capacity:
            # Unless it would result in an empty resultset we don't want to show rooms with >20% more capacity
            # than requested. This cannot be done easily in SQL so we do that logic here after the SQL query already
            # weeded out rooms that are too small
            matching_capacity_rooms = [r for r in rooms if r.capacity is None or r.capacity <= capacity * 1.2]
            if matching_capacity_rooms:
                rooms = matching_capacity_rooms
        return rooms

    def has_live_reservations(self):
        return self.reservations.filter_by(
            is_archived=False,
            is_cancelled=False,
            is_rejected=False
        ).count() > 0

    def get_blocked_rooms(self, *dates, **kwargs):
        states = kwargs.get('states', (BlockedRoom.State.accepted,))
        return (self.blocked_rooms
                .join(BlockedRoom.blocking)
                .options(contains_eager(BlockedRoom.blocking))
                .filter(or_(Blocking.is_active_at(d) for d in dates),
                        BlockedRoom.state.in_(states))
                .all())

    @property
    def protection_parent(self):
        return None

    @staticmethod
    def is_user_admin(user):
        return rb_is_admin(user)

    @classmethod
    def get_permissions_for_user(cls, user, allow_admin=True):
        """Get the permissions for all rooms for a user.

        In case of multipass-based groups it will try to get a list of
        all groups the user is in, and if that's not possible check the
        permissions one by one for each room (which may result in many
        group membership lookups).

        It is recommended to not call this in any place where performance
        matters and to memoize the result.
        """
        # XXX: When changing the logic in here, make sure to update can_* as well!
        all_rooms_query = (Room.query
                           .filter(Room.is_active)
                           .options(load_only('id', 'protection_mode', 'reservations_need_confirmation',
                                              'is_reservable'),
                                    raiseload('owner'),
                                    joinedload('acl_entries')))
        is_admin = allow_admin and cls.is_user_admin(user)
        if (is_admin and allow_admin) or not user.can_get_all_multipass_groups:
            # check one by one if we can't get a list of all groups the user is in
            return {r.id: {
                'book': r.can_book(user, allow_admin=allow_admin),
                'prebook': r.can_prebook(user, allow_admin=allow_admin),
                'override': r.can_override(user, allow_admin=allow_admin),
                'moderate': r.can_moderate(user, allow_admin=allow_admin),
                'manage': r.can_manage(user, allow_admin=allow_admin),
            } for r in all_rooms_query}

        criteria = [db.and_(RoomPrincipal.type == PrincipalType.user, RoomPrincipal.user_id == user.id)]
        for group in user.local_groups:
            criteria.append(db.and_(RoomPrincipal.type == PrincipalType.local_group,
                                    RoomPrincipal.local_group_id == group.id))
        for group in user.iter_all_multipass_groups():
            criteria.append(db.and_(RoomPrincipal.type == PrincipalType.multipass_group,
                                    RoomPrincipal.multipass_group_provider == group.provider.name,
                                    db.func.lower(RoomPrincipal.multipass_group_name) == group.name.lower()))

        data = {}
        permissions = {'book', 'prebook', 'override', 'moderate', 'manage'}
        prebooking_required_rooms = set()
        non_reservable_rooms = set()
        for room in all_rooms_query:
            data[room.id] = {x: False for x in permissions}
            if room.reservations_need_confirmation:
                prebooking_required_rooms.add(room.id)
            if not room.is_reservable:
                non_reservable_rooms.add(room.id)
            if (room.is_reservable and room.is_public) or (is_admin and allow_admin):
                if not room.reservations_need_confirmation or (is_admin and allow_admin):
                    data[room.id]['book'] = True
                if room.reservations_need_confirmation:
                    data[room.id]['prebook'] = True
            if is_admin and allow_admin:
                data[room.id]['override'] = True
                data[room.id]['moderate'] = True
                data[room.id]['manage'] = True
        query = (RoomPrincipal.query
                 .join(Room)
                 .filter(Room.is_active, db.or_(*criteria))
                 .options(load_only('room_id', 'full_access', 'permissions')))
        for principal in query:
            is_reservable = principal.room_id not in non_reservable_rooms
            for permission in permissions:
                if not is_reservable and not (is_admin and allow_admin) and permission in ('book', 'prebook'):
                    continue
                explicit = permission == 'prebook' and principal.room_id not in prebooking_required_rooms
                check_permission = None if permission == 'manage' else permission
                if principal.has_management_permission(check_permission, explicit=explicit):
                    data[principal.room_id][permission] = True
        return data

    def can_access(self, user, allow_admin=True):
        # rooms are never access-restricted
        raise NotImplementedError

    def can_book(self, user, allow_admin=True):
        # XXX: When changing the logic in here, make sure to update get_permissions_for_user as well!
        if not user:
            return False
        if not self.is_reservable and not (allow_admin and self.is_user_admin(user)):
            return False
        if self.is_public and not self.reservations_need_confirmation:
            return True
        return self.can_manage(user, permission='book', allow_admin=allow_admin)

    def can_prebook(self, user, allow_admin=True):
        # XXX: When changing the logic in here, make sure to update get_permissions_for_user as well!
        if not user:
            return False
        if not self.is_reservable and not (allow_admin and self.is_user_admin(user)):
            return False
        if self.is_public and self.reservations_need_confirmation:
            return True
        # When the room does not use prebookings, we do not want the prebook option to show
        # up for admins or room managers unless they are actually in the ACL with the prebook
        # permission.
        explicit = not self.reservations_need_confirmation
        return self.can_manage(user, permission='prebook', allow_admin=allow_admin, explicit_permission=explicit)

    def can_override(self, user, allow_admin=True):
        # XXX: When changing the logic in here, make sure to update get_permissions_for_user as well!
        return self.can_manage(user, permission='override', allow_admin=allow_admin)

    def can_moderate(self, user, allow_admin=True):
        # XXX: When changing the logic in here, make sure to update get_permissions_for_user as well!
        return self.can_manage(user, permission='moderate', allow_admin=allow_admin)

    def can_edit(self, user):
        if not user:
            return False
        return rb_is_admin(user)

    def can_delete(self, user):
        if not user:
            return False
        return rb_is_admin(user)

    @unify_user_args
    @cached(_cache)
    def is_owned_by(self, user):
        """Checks if the user is managing the room (owner or manager)"""
        if self.owner == user:
            return True
        manager_group = self.get_attribute_value('manager-group')
        if not manager_group:
            return False
        return user in GroupProxy.get_named_default_group(manager_group)

    @classmethod
    def get_owned_by(cls, user):
        return [room for room in cls.find(is_active=True) if room.is_owned_by(user)]

    @classmethod
    def user_owns_rooms(cls, user):
        return any(room for room in cls.find(is_active=True) if room.is_owned_by(user))

    def check_advance_days(self, end_date, user=None, quiet=False):
        if not self.max_advance_days:
            return True
        if user and (rb_is_admin(user) or self.is_owned_by(user)):
            return True
        advance_days = (end_date - date.today()).days
        ok = advance_days < self.max_advance_days
        if quiet or ok:
            return ok
        else:
            msg = _(u'You cannot book this room more than {} days in advance')
            raise NoReportError(msg.format(self.max_advance_days))

    def check_bookable_hours(self, start_time, end_time, user=None, quiet=False):
        if user and (rb_is_admin(user) or self.is_owned_by(user)):
            return True
        bookable_hours = self.bookable_hours.all()
        if not bookable_hours:
            return True
        for bt in bookable_hours:
            if bt.fits_period(start_time, end_time):
                return True
        if quiet:
            return False
        raise NoReportError(u'Room cannot be booked at this time')


Room.register_protection_events()
