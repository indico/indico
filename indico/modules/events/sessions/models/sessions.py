# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db.sqlalchemy.locations import LocationMixin
from indico.core.db.sqlalchemy.protection import ProtectionManagersMixin
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.core.db.sqlalchemy.util.queries import increment_and_get

from indico.core.db import db
from indico.util.string import format_repr, return_ascii


def _get_next_friendly_id(context):
    """Get the next friendly id for a contribution."""
    from indico.modules.events import Event
    event_id = context.current_parameters['event_id']
    assert event_id is not None
    return increment_and_get(Event._last_friendly_session_id, Event.id == event_id)


class Session(ProtectionManagersMixin, LocationMixin, db.Model):
    __tablename__ = 'sessions'
    __auto_table_args = {'schema': 'events'}
    location_backref_name = 'sessions'
    disallowed_protection_modes = frozenset()

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls)

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The human-friendly ID for the contribution
    friendly_id = db.Column(
        db.Integer,
        nullable=False,
        default=_get_next_friendly_id
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    title = db.Column(
        db.String,
        nullable=False
    )
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    event_new = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'sessions',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )
    acl_entries = db.relationship(
        'SessionPrincipal',
        lazy=True,
        cascade='all, delete-orphan',
        collection_class=set,
        backref='session'
    )
    blocks = db.relationship(
        'SessionBlock',
        lazy=True,
        cascade='all, delete-orphan',
        backref=db.backref(
            'session',
            lazy=False
        )
    )

    # relationship backrefs:
    # - contributions (Contribution.session)
    # - legacy_mapping (LegacySessionMapping.session)

    @property
    def location_parent(self):
        return self.event_new

    @property
    def protection_parent(self):
        return self.event_new

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', is_deleted=False, _text=self.title)
