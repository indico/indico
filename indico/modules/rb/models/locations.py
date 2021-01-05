# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import re

from sqlalchemy.ext.hybrid import hybrid_property

from indico.core.db import db
from indico.util.string import format_repr, return_ascii


class Location(db.Model):
    __tablename__ = 'locations'
    __table_args__ = (db.Index(None, 'name', unique=True, postgresql_where=db.text('NOT is_deleted')),
                      {'schema': 'roombooking'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    name = db.Column(
        db.String,
        nullable=False,
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
        default='%1$s/%2$s-%3$s'
    )
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    #: The format used to display room names (with placeholders)
    @hybrid_property
    def room_name_format(self):
        """Translate Postgres' format syntax (e.g. `%1$s/%2$s-%3$s`) to Python's."""
        placeholders = ['building', 'floor', 'number']
        return re.sub(
            r'%(\d)\$s',
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

    rooms = db.relationship(
        'Room',
        back_populates='location',
        cascade='all, delete-orphan',
        primaryjoin='(Room.location_id == Location.id) & ~Room.is_deleted',
        lazy=True
    )

    # relationship backrefs:
    # - breaks (Break.own_venue)
    # - contributions (Contribution.own_venue)
    # - events (Event.own_venue)
    # - session_blocks (SessionBlock.own_venue)
    # - sessions (Session.own_venue)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'name', is_deleted=False)
