# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db
from indico.util.string import format_repr, return_ascii


class LegacySessionMapping(db.Model):
    """Legacy session id mapping.

    Legacy sessions had ids unique only within their event.
    Additionally, some very old sessions had non-numeric IDs.
    This table maps those ids to the new globally unique session id.
    """

    __tablename__ = 'legacy_session_id_map'
    __table_args__ = {'schema': 'events'}

    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        primary_key=True,
        autoincrement=False
    )
    legacy_session_id = db.Column(
        db.String,
        primary_key=True
    )
    session_id = db.Column(
        db.Integer,
        db.ForeignKey('events.sessions.id'),
        nullable=False,
        index=True
    )

    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'legacy_session_mappings',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )
    session = db.relationship(
        'Session',
        lazy=False,
        backref=db.backref(
            'legacy_mapping',
            cascade='all, delete-orphan',
            uselist=False,
            lazy=True
        )
    )

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'event_id', 'legacy_session_id', 'session_id')


class LegacySessionBlockMapping(db.Model):
    """Legacy session block id mapping.

    Legacy sessions blocks had ids unique only within their session.
    """

    __tablename__ = 'legacy_session_block_id_map'
    __table_args__ = {'schema': 'events'}

    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        primary_key=True,
        autoincrement=False
    )
    legacy_session_id = db.Column(
        db.String,
        primary_key=True
    )
    legacy_session_block_id = db.Column(
        db.String,
        primary_key=True
    )
    session_block_id = db.Column(
        db.Integer,
        db.ForeignKey('events.session_blocks.id'),
        nullable=False,
        index=True
    )

    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'legacy_session_block_mappings',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )
    session_block = db.relationship(
        'SessionBlock',
        lazy=False,
        backref=db.backref(
            'legacy_mapping',
            cascade='all, delete-orphan',
            uselist=False,
            lazy=True
        )
    )

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'event_id', 'legacy_session_id', 'legacy_session_block_id', 'session_block_id')
