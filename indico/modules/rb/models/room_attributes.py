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
Attribute keys for rooms and reservations
"""

from indico.core.db import db
from indico.util.string import return_ascii
from indico.modules.rb.models.utils import JSONStringBridgeMixin


class RoomAttributeAssociation(JSONStringBridgeMixin, db.Model):
    __tablename__ = 'rooms_attributes_association'

    # columns

    attribute_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'room_attributes.id',
        ),
        primary_key=True
    )
    room_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'rooms.id',
        ),
        primary_key=True
    )
    raw_data = db.Column(
        db.String
    )

    # relationships

    attribute = db.relationship(
        'RoomAttribute',
        backref='room_assocs'
    )

    def __init__(self, *args, **kwargs):
        value = kwargs.pop('value', None)
        super(RoomAttributeAssociation, self).__init__(*args, **kwargs)
        if value is not None:
            self.value = value


class RoomAttribute(JSONStringBridgeMixin, db.Model):
    __tablename__ = 'room_attributes'
    __table_args__ = (db.UniqueConstraint('name', 'location_id'),)

    # columns

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    parent_id = db.Column(
        db.Integer,
        db.ForeignKey('room_attributes.id')
    )
    name = db.Column(
        db.String,
        nullable=False,
        index=True
    )
    title = db.Column(
        db.String,
        nullable=False
    )
    location_id = db.Column(
        db.Integer,
        db.ForeignKey('locations.id'),
        nullable=False
    )
    raw_data = db.Column(
        db.String
    )

    # relationships

    children = db.relationship(
        'RoomAttribute',
        backref=db.backref(
            'parent',
            remote_side=[id]
        )
    )

    @return_ascii
    def __repr__(self):
        return u'<RoomAttribute({0}, {1}, {2}, {3})>'.format(
            self.id,
            self.name,
            self.location_id,
            self.raw_data
        )
