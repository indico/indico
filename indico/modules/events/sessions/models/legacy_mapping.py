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

from __future__ import unicode_literals

from indico.core.db import db
from indico.util.string import format_repr, return_ascii


class LegacySessionMapping(db.Model):
    """Legacy session id mapping

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

    event_new = db.relationship(
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
    """Legacy session block id mapping

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

    event_new = db.relationship(
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
