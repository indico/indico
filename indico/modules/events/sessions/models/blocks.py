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

from indico.core.db import db
from indico.core.db.sqlalchemy.locations import LocationMixin
from indico.core.db.sqlalchemy.protection import ProtectionManagersMixin, ProtectionMode
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.util.string import format_repr, return_ascii


class SessionBlock(ProtectionManagersMixin, LocationMixin, db.Model):
    __tablename__ = 'session_blocks'
    __auto_table_args = (db.UniqueConstraint('id', 'session_id'),  # useless but needed for the compound fkey
                         {'schema': 'events'})
    location_backref_name = 'session_blocks'
    disallowed_protection_modes = frozenset({ProtectionMode.public, ProtectionMode.protected})

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls)

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    session_id = db.Column(
        db.Integer,
        db.ForeignKey('events.sessions.id'),
        index=True,
        nullable=False
    )
    title = db.Column(
        db.String,
        nullable=False,
        default=''
    )
    duration = db.Column(
        db.Interval,
        nullable=False
    )

    acl_entries = db.relationship(
        'SessionBlockPrincipal',
        lazy=True,
        cascade='all, delete-orphan',
        collection_class=set,
        backref='session_block'
    )

    # relationship backrefs:
    # - contributions (Contribution.session_block)
    # - session (Session.blocks)

    @property
    def location_parent(self):
        return self.session

    @property
    def protection_parent(self):
        return self.session

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', _text=self.title or None)
