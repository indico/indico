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
Custom attributes for rooms
"""
import json

from sqlalchemy.ext.hybrid import hybrid_property

from indico.core.db import db


class RoomAttribute(db.Model):
    __tablename__ = 'room_attributes'
    __table_args__ = (
        db.ForeignKeyConstraint(
            ['parent_key_id', 'parent_room_id'],
            ['room_attributes.key_id', 'room_attributes.room_id']
        ),
        {}
    )

    key_id = db.Column(
        db.Integer,
        db.ForeignKey('room_attribute_keys.id'),
        nullable=False,
        primary_key=True
    )

    raw_data = db.Column(
        db.String,
        nullable=False
    )

    room_id = db.Column(
        db.Integer,
        db.ForeignKey('rooms.id'),
        nullable=False,
        primary_key=True
    )

    parent_key_id = db.Column(
        db.Integer
    )

    parent_room_id = db.Column(
        db.Integer,
    )

    children = db.relationship(
        'RoomAttribute',
        backref=db.backref('parent', remote_side=[key_id, room_id])
    )

    @hybrid_property
    def value(self):
        return json.loads(self.raw_data)

    @value.setter
    def value(self, data):
        self.raw_data = json.dumps(data)

    def __repr__(self):
        return '<RoomAttribute({0}, {1}, {2})>'.format(self.room_id,
                                                       self.key_id,
                                                       self.value)
