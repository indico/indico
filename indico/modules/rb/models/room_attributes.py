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

from sqlalchemy.dialects.postgresql import JSON

from indico.core.db import db
from indico.util.string import return_ascii


class RoomAttributeAssociation(db.Model):
    __tablename__ = 'room_attribute_values'
    __table_args__ = {'schema': 'roombooking'}

    attribute_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'roombooking.room_attributes.id',
        ),
        primary_key=True
    )
    room_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'roombooking.rooms.id',
        ),
        primary_key=True
    )
    value = db.Column(
        JSON
    )

    attribute = db.relationship(
        'RoomAttribute',
        backref=db.backref(
            'room_associations',
            cascade='all, delete-orphan'
        )
    )

    # relationship backrefs:
    # - room (Room.attributes)

    @return_ascii
    def __repr__(self):
        return u'<RoomAttributeAssociation({0}, {1}, {2})>'.format(self.room_id, self.attribute.name, self.value)


class RoomAttribute(db.Model):
    __tablename__ = 'room_attributes'
    __table_args__ = (db.UniqueConstraint('name', 'location_id'),
                      {'schema': 'roombooking'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    parent_id = db.Column(
        db.Integer,
        db.ForeignKey('roombooking.room_attributes.id')
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
        db.ForeignKey('roombooking.locations.id'),
        nullable=False
    )
    type = db.Column(
        db.String,
        nullable=False
    )
    is_required = db.Column(
        db.Boolean,
        nullable=False
    )
    is_hidden = db.Column(
        db.Boolean,
        nullable=False
    )

    children = db.relationship(
        'RoomAttribute',
        backref=db.backref(
            'parent',
            remote_side=[id]
        )
    )

    # relationship backrefs:
    # - location (Location.attributes)
    # - parent (RoomAttribute.children)
    # - room_associations (RoomAttributeAssociation.attribute)

    @return_ascii
    def __repr__(self):
        return u'<RoomAttribute({}, {}, {})>'.format(self.id, self.name, self.location.name)
