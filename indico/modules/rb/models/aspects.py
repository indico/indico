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

from indico.core.db import db
from indico.util.serializer import Serializer
from indico.util.string import return_ascii


class Aspect(db.Model, Serializer):
    __tablename__ = 'aspects'
    __table_args__ = {'schema': 'roombooking'}
    __public__ = ('id', 'name', 'center_latitude', 'center_longitude', 'zoom_level', 'top_left_latitude',
                  'top_left_longitude', 'bottom_right_latitude', 'bottom_right_longitude', 'default_on_startup')

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    name = db.Column(
        db.String,
        nullable=False
    )
    center_latitude = db.Column(
        db.String,
        nullable=False
    )
    center_longitude = db.Column(
        db.String,
        nullable=False
    )
    zoom_level = db.Column(
        db.SmallInteger,
        nullable=False
    )
    top_left_latitude = db.Column(
        db.String,
        nullable=False
    )
    top_left_longitude = db.Column(
        db.String,
        nullable=False
    )
    bottom_right_latitude = db.Column(
        db.String,
        nullable=False
    )
    bottom_right_longitude = db.Column(
        db.String,
        nullable=False
    )
    location_id = db.Column(
        db.Integer,
        db.ForeignKey('roombooking.locations.id'),
        nullable=False
    )

    # relationship backrefs:
    # - location (Location.aspects)

    @return_ascii
    def __repr__(self):
        return u'<Aspect({0}, {1}, {2})>'.format(
            self.id,
            self.location_id,
            self.name
        )

    @property
    def default_on_startup(self):
        return self.id == self.location.default_aspect_id
