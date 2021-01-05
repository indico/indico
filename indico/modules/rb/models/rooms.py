# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import warnings
from datetime import date, time

from sqlalchemy import and_, or_
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import contains_eager, joinedload, load_only

from indico.core.db.sqlalchemy import db
from indico.core.db.sqlalchemy.custom import static_array
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.db.sqlalchemy.protection import ProtectionManagersMixin, ProtectionMode
from indico.core.db.sqlalchemy.util.queries import db_dates_overlap
from indico.core.errors import NoReportError
from indico.legacy.common.cache import GenericCache
from indico.modules.rb.models.blocked_rooms import BlockedRoom
from indico.modules.rb.models.blockings import Blocking
from indico.modules.rb.models.equipment import EquipmentType, RoomEquipmentAssociation
from indico.modules.rb.models.favorites import favorite_room_table
from indico.modules.rb.models.principals import RoomPrincipal
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.room_attributes import RoomAttribute, RoomAttributeAssociation
from indico.modules.rb.models.room_bookable_hours import BookableHours
from indico.modules.rb.models.room_nonbookable_periods import NonBookablePeriod
from indico.modules.rb.util import rb_is_admin
from indico.util.i18n import _
from indico.util.serializer import Serializer
from indico.util.string import format_repr, natural_sort_key, return_ascii
from indico.web.flask.util import url_for


_cache = GenericCache('Rooms')


class Room(ProtectionManagersMixin, db.Model, Serializer):
    __tablename__ = 'rooms'
    __table_args__ = (db.UniqueConstraint('id', 'location_id'),  # useless but needed for the LocationMixin fkey
                      db.CheckConstraint("verbose_name != ''", 'verbose_name_not_empty'),
                      {'schema': 'roombooking'})

    default_protection_mode = ProtectionMode.public
    disallowed_protection_modes = frozenset({ProtectionMode.inheriting})

    __api_public__ = (
        'id', 'building', 'name', 'floor', 'longitude', 'latitude', ('number', 'roomNr'), ('location_name', 'location'),
        ('full_name', 'fullName')
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
    notification_emails = db.Column(
        ARRAY(db.String),
        nullable=False,
        default=[]
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
    end_notification_daily = db.Column(
        db.Integer,
        nullable=True
    )
    end_notification_weekly = db.Column(
        db.Integer,
        nullable=True
    )
    end_notification_monthly = db.Column(
        db.Integer,
        nullable=True
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
    end_notifications_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    telephone = db.Column(
        db.String,
        nullable=False,
        default=''
    )
    key_location = db.Column(
        db.String,
        nullable=False,
        default=''
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
        db.String,
        nullable=False,
        default=''
    )
    owner_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=False
    )
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
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

    location = db.relationship(
        'Location',
        back_populates='rooms',
        lazy=True
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

    #: The owner of the room. This is purely informational and does not grant
    #: any permissions on the room.
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
    # - session_blocks (SessionBlock.own_room)
    # - sessions (Session.own_room)

    @hybrid_property
    def is_auto_confirm(self):
        return not self.reservations_need_confirmation

    @is_auto_confirm.expression
    def is_auto_confirm(self):
        return ~self.reservations_need_confirmation

    @property
    def details_url(self):
        if self.id is None:
            return None
        return url_for('rb.room_link', room_id=self.id)

    @property
    def map_url(self):
        if not self.location.map_url_template:
            return None
        return self.location.map_url_template.format(
            id=self.id,
            building=self.building,
            floor=self.floor,
            number=self.number,
            lat=self.latitude,
            lng=self.longitude,
        )

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
    def location_name(self):
        return self.location.name

    @property
    def sprite_position(self):
        sprite_mapping = _cache.get('rooms-sprite-mapping')
        return sprite_mapping.get(self.id, 0) if sprite_mapping else 0  # placeholder at position 0

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'full_name', is_deleted=False)

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
        """Retrieve rooms, sorted by location and full name."""
        rooms = super(Room, cls).find_all(*args, **kwargs)
        rooms.sort(key=lambda r: natural_sort_key(r.location_name + r.full_name))
        return rooms

    @classmethod
    def find_with_attribute(cls, attribute):
        """Search rooms which have a specific attribute."""
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
            query = query.filter(~Room.is_deleted)
        if filters:  # pragma: no cover
            query = query.filter(*filters)
        if order:  # pragma: no cover
            query = query.order_by(*order)

        keys = ('room',) + tuple(args)
        return (dict(zip(keys, row if args else [row])) for row in query)

    @staticmethod
    def filter_available(start_dt, end_dt, repetition, include_blockings=True, include_pre_bookings=True,
                         include_pending_blockings=False):
        """Return a SQLAlchemy filter criterion ensuring that the room is available during the given time."""
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
                           .filter(~Room.is_deleted)
                           .options(load_only('id', 'protection_mode', 'reservations_need_confirmation',
                                              'is_reservable', 'owner_id'),
                                    joinedload('owner').load_only('id'),
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
            is_owner = user == room.owner
            data[room.id] = {x: False for x in permissions}
            if room.reservations_need_confirmation:
                prebooking_required_rooms.add(room.id)
            if not room.is_reservable:
                non_reservable_rooms.add(room.id)
            if (room.is_reservable and (room.is_public or is_owner)) or (is_admin and allow_admin):
                if not room.reservations_need_confirmation or is_owner or (is_admin and allow_admin):
                    data[room.id]['book'] = True
                if room.reservations_need_confirmation:
                    data[room.id]['prebook'] = True
            if is_owner or (is_admin and allow_admin):
                data[room.id]['override'] = True
                data[room.id]['moderate'] = True
                data[room.id]['manage'] = True
        query = (RoomPrincipal.query
                 .join(Room)
                 .filter(~Room.is_deleted, db.or_(*criteria))
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

    def can_manage(self, user, permission=None, allow_admin=True, check_parent=True, explicit_permission=False):
        if user and user == self.owner and (permission is None or not explicit_permission):
            return True
        return super(Room, self).can_manage(user, permission=permission, allow_admin=allow_admin,
                                            check_parent=check_parent, explicit_permission=explicit_permission)

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

    def check_advance_days(self, end_date, user=None, quiet=False):
        if not self.max_advance_days:
            return True
        if user and (rb_is_admin(user) or self.can_manage(user)):
            return True
        advance_days = (end_date - date.today()).days
        ok = advance_days < self.max_advance_days
        if quiet or ok:
            return ok
        else:
            msg = _(u'You cannot book this room more than {} days in advance')
            raise NoReportError(msg.format(self.max_advance_days))

    def check_bookable_hours(self, start_time, end_time, user=None, quiet=False):
        if user and (rb_is_admin(user) or self.can_manage(user)):
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
