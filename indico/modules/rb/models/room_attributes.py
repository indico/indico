# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.dialects.postgresql import JSONB

from indico.core.db import db
from indico.util.string import format_repr, return_ascii


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
        JSONB
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
    __table_args__ = {'schema': 'roombooking'}

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    name = db.Column(
        db.String,
        nullable=False,
        index=True,
        unique=True
    )
    title = db.Column(
        db.String,
        nullable=False
    )
    is_hidden = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    # relationship backrefs:
    # - room_associations (RoomAttributeAssociation.attribute)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'name')
