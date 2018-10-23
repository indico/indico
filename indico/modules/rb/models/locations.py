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

import re
from collections import defaultdict
from datetime import time

from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_property

from indico.core.db import db
from indico.modules.rb.models.aspects import Aspect
from indico.util.caching import memoize_request
from indico.util.decorators import classproperty
from indico.util.i18n import _
from indico.util.locators import locator_property
from indico.util.string import return_ascii


ROOM_NAME_TPL_RE = re.compile(r'%(\d)\$s')


class Location(db.Model):
    __tablename__ = 'locations'
    __table_args__ = {'schema': 'roombooking'}

    # TODO: Turn this into a proper admin setting
    working_time_periods = ((time(8, 30), time(12, 30)), (time(13, 30), time(17, 30)))

    @classproperty
    @classmethod
    def working_time_start(cls):
        return cls.working_time_periods[0][0]

    @classproperty
    @classmethod
    def working_time_end(cls):
        return cls.working_time_periods[-1][1]

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    name = db.Column(
        db.String,
        nullable=False,
        unique=True,
        index=True
    )
    is_default = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    default_aspect_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'roombooking.aspects.id',
            use_alter=True,
            name='fk_locations_default_aspect_id',
            onupdate='CASCADE',
            ondelete='SET NULL'
        )
    )
    map_url_template = db.Column(
        db.String,
        nullable=False,
        default=''
    )
    _room_name_format = db.Column(
        'room_name_format',
        db.String,
        nullable=False,
        default=u'%1$s/%2$s-%3$s'
    )

    #: The format used to display room names (with placeholders)
    @hybrid_property
    def room_name_format(self):
        """Translate Postgres' format syntax (e.g. `%1$s/%2$s-%3$s`) to Python's."""
        placeholders = ['building', 'floor', 'number']
        return ROOM_NAME_TPL_RE.sub(
            lambda m: '{%s}' % placeholders[int(m.group(1)) - 1],
            self._room_name_format
        )
    @room_name_format.expression
    def room_name_format(cls):
        return cls._room_name_format

    @room_name_format.setter
    def room_name_format(self, value):
        self._room_name_format = value.format(
            building='%1$s',
            floor='%2$s',
            number='%3$s'
        )

    aspects = db.relationship(
        'Aspect',
        backref='location',
        cascade='all, delete-orphan',
        primaryjoin=(id == Aspect.location_id),
        lazy='dynamic',
    )

    default_aspect = db.relationship(
        'Aspect',
        primaryjoin=default_aspect_id == Aspect.id,
        post_update=True,
    )

    rooms = db.relationship(
        'Room',
        backref='location',
        cascade='all, delete-orphan',
        lazy=True
    )

    attributes = db.relationship(
        'RoomAttribute',
        backref='location',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    equipment_types = db.relationship(
        'EquipmentType',
        backref='location',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    holidays = db.relationship(
        'Holiday',
        backref='location',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    # relationship backrefs:
    # - breaks (Break.own_venue)
    # - contributions (Contribution.own_venue)
    # - events (Event.own_venue)
    # - session_blocks (SessionBlock.own_venue)
    # - sessions (Session.own_venue)

    @return_ascii
    def __repr__(self):
        return u'<Location({0}, {1}, {2})>'.format(
            self.id,
            self.default_aspect_id,
            self.name
        )

    @locator_property
    def locator(self):
        return {'locationId': self.name}

    @property
    @memoize_request
    def is_map_available(self):
        return self.aspects.count() > 0

    @classproperty
    @classmethod
    @memoize_request
    def default_location(cls):
        return cls.query.filter_by(is_default=True).first()

    def set_default(self):
        if self.is_default:
            return
        (Location.query
         .filter(Location.is_default | (Location.id == self.id))
         .update({'is_default': func.not_(Location.is_default)}, synchronize_session='fetch'))

    def get_attribute_by_name(self, name):
        return self.attributes.filter_by(name=name).first()

    def get_equipment_by_name(self, name):
        return self.equipment_types.filter_by(name=name).first()

    def get_buildings(self):
        building_rooms = defaultdict(list)
        for room in self.rooms:
            building_rooms[room.building].append(room)

        buildings = []
        for building_name, rooms in building_rooms.iteritems():
            room_with_lat_lon = next((r for r in rooms if r.longitude and r.latitude), None)
            if not room_with_lat_lon:
                continue
            buildings.append({'number': building_name,
                              'title': _(u'Building {}'.format(building_name)),
                              'longitude': room_with_lat_lon.longitude,
                              'latitude': room_with_lat_lon.latitude,
                              'rooms': [r.to_serializable('__public_exhaustive__') for r in rooms]})
        return buildings
