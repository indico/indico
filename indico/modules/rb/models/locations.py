# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re

from sqlalchemy.ext.hybrid import hybrid_property

from indico.core.db import db
from indico.core.db.sqlalchemy.protection import ProtectionManagersMixin
from indico.util.string import format_repr


class Location(ProtectionManagersMixin, db.Model):
    __tablename__ = 'locations'
    __table_args__ = (db.Index(None, 'name', unique=True, postgresql_where=db.text('NOT is_deleted')),
                      {'schema': 'roombooking'})

    disable_protection_mode = True

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
        placeholders = ['building', 'floor', 'number', 'site']
        return re.sub(
            r'%(\d)\$s',
            lambda m: '{%s}' % placeholders[int(m.group(1)) - 1],  # noqa: UP031
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
            number='%3$s',
            site='%4$s'
        )

    rooms = db.relationship(
        'Room',
        back_populates='location',
        cascade='all, delete-orphan',
        primaryjoin='(Room.location_id == Location.id) & ~Room.is_deleted',
        lazy=True
    )

    acl_entries = db.relationship(
        'LocationPrincipal',
        lazy=True,
        backref='location',
        cascade='all, delete-orphan',
        collection_class=set
    )

    # relationship backrefs:
    # - breaks (Break.own_venue)
    # - contributions (Contribution.own_venue)
    # - events (Event.own_venue)
    # - session_blocks (SessionBlock.own_venue)
    # - sessions (Session.own_venue)

    def __repr__(self):
        return format_repr(self, 'id', 'name', is_deleted=False)

    @property
    def protection_parent(self):
        return None

    @staticmethod
    def is_user_admin(user):
        from indico.modules.rb.util import rb_is_admin

        return rb_is_admin(user)

    def can_delete(self, user):
        from indico.modules.rb.util import rb_is_admin

        if not user:
            return False
        return rb_is_admin(user)
