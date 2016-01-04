# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.util.decorators import strict_classproperty


class LocationMixin(object):
    """Mixin to store location information in a model.

    A location in this context can be either a reference to a room in
    the roombooking module or a room and location name.

    In case the location is inherited, the `location_parent` property
    is used to determine the parent object from which the location is
    inherited (which may also inherit its location).
    """

    #: The name of the backref added to the `Room` model for items
    #: which are associated with that room.
    location_backref_name = None
    #: Whether the item can inherit its location from a parent.  If
    #: this is ``False``, `location_parent` should not be overridden.
    allow_location_inheritance = True

    @strict_classproperty
    @classmethod
    def __auto_table_args(cls):
        checks = [db.CheckConstraint("(room_id IS NULL) OR (venue_name = '' AND room_name = '')",
                                     'no_custom_location_if_room')]
        if cls.allow_location_inheritance:
            checks.append(db.CheckConstraint("NOT inherit_location OR (room_id IS NULL AND venue_name = '' AND "
                                             "room_name = '' AND address = '')", 'inherited_location'))
        return tuple(checks)

    @property
    def location_parent(self):
        """The parent object to consult if the location is inherited."""
        if not self.allow_location_inheritance:
            return None
        raise NotImplementedError

    @declared_attr
    def inherit_location(cls):
        if cls.allow_location_inheritance:
            return db.Column(
                db.Boolean,
                nullable=False,
                default=True
            )
        else:
            return False

    @declared_attr
    def own_room_id(cls):
        return db.Column(
            'room_id',
            db.Integer,
            db.ForeignKey('roombooking.rooms.id'),
            nullable=True,
            index=True
        )

    @declared_attr
    def own_venue_name(cls):
        return db.Column(
            'venue_name',
            db.String,
            nullable=False,
            default=''
        )

    @declared_attr
    def own_room_name(cls):
        return db.Column(
            'room_name',
            db.String,
            nullable=False,
            default=''
        )

    @declared_attr
    def own_address(cls):
        return db.Column(
            'address',
            db.Text,
            nullable=False,
            default=''
        )

    @declared_attr
    def own_room(cls):
        return db.relationship(
            'Room',
            lazy=True,
            backref=db.backref(
                cls.location_backref_name,
                lazy='dynamic'
            )
        )

    @property
    def room(self):
        """The Room where this item is located.

        This is ``None`` if a custom room name was entered.
        """
        if self.inherit_location and self.location_parent is None:
            return None
        return self.own_room if not self.inherit_location else self.location_parent.room

    @room.setter
    def room(self, room):
        self.own_room = room

    @property
    def venue_name(self):
        """The name of the location where this item is located."""
        if self.inherit_location and self.location_parent is None:
            return ''
        room = self.room
        if room is not None:
            return room.location.name
        return self.own_venue_name if not self.inherit_location else self.location_parent.venue_name

    @venue_name.setter
    def venue_name(self, venue_name):
        self.own_venue_name = venue_name

    @property
    def room_name(self):
        """The name of the room where this item is located."""
        if self.inherit_location and self.location_parent is None:
            return ''
        room = self.room
        if room is not None:
            return room.name
        return self.own_room_name if not self.inherit_location else self.location_parent.room_name

    @room_name.setter
    def room_name(self, room_name):
        self.own_room_name = room_name

    @property
    def address(self):
        """The address where this item is located."""
        if self.inherit_location and self.location_parent is None:
            return ''
        return self.own_address if not self.inherit_location else self.location_parent.address

    @address.setter
    def address(self, address):
        self.own_address = address

    @property
    def location_data(self):
        """All location data for the item.

        Returns a dict containing ``source``, ``inheriting``, ``room``,
        ``room_name``, ``venue_name`` and ``address``.  The
        ``source`` is the object the location data is taken from, i.e.
        either the item itself or the object the location data is
        inherited from.
        """
        data_source = self
        while data_source and data_source.inherit_location:
            data_source = data_source.location_parent
        if data_source is None:
            return {'source': None, 'room': None, 'room_name': '', 'venue_name': '', 'address': '',
                    'inheriting': False}
        else:
            return {'source': data_source, 'room': data_source.room, 'room_name': data_source.room_name,
                    'venue_name': data_source.venue_name, 'address': data_source.address,
                    'inheriting': self.inherit_location}
