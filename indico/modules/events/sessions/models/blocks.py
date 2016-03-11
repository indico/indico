# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.modules.events.sessions.util import session_coordinator_priv_enabled
from indico.util.string import format_repr, return_ascii


class SessionBlock(LocationMixin, db.Model):
    __tablename__ = 'session_blocks'
    __auto_table_args = (db.UniqueConstraint('id', 'session_id'),  # useless but needed for the compound fkey
                         {'schema': 'events'})
    location_backref_name = 'session_blocks'

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

    #: Persons associated with this contribution
    person_links = db.relationship(
        'SessionBlockPersonLink',
        lazy=True,
        cascade='all, delete-orphan',
        backref=db.backref(
            'session_block',
            lazy=True
        )
    )

    # relationship backrefs:
    # - contributions (Contribution.session_block)
    # - session (Session.blocks)
    # - timetable_entry (TimetableEntry.session_block)

    @declared_attr
    def contribution_count(cls):
        from indico.modules.events.contributions.models.contributions import Contribution
        query = (db.select([db.func.count(Contribution.id)])
                 .where((Contribution.session_block_id == cls.id) & ~Contribution.is_deleted)
                 .correlate_except(Contribution))
        return db.column_property(query, deferred=True)

    def __init__(self, **kwargs):
        # explicitly initialize those relationships with None to avoid
        # an extra query to check whether there is an object associated
        # when assigning a new one (e.g. during cloning)
        kwargs.setdefault('timetable_entry', None)
        super(SessionBlock, self).__init__(**kwargs)

    @property
    def event_new(self):
        return self.session.event_new

    @property
    def location_parent(self):
        return self.session

    def can_access(self, user, allow_admin=True):
        return self.session.can_access(user, allow_admin=allow_admin)

    def can_manage(self, user, allow_admin=True):
        """Check whether a user can manage this session block.

        This only applies to the block itself, not to contributions inside it.
        """
        if user is None:
            return False
        # full session manager can always manage blocks. this also includes event managers and higher.
        elif self.session.can_manage(user, allow_admin=allow_admin):
            return True
        # session coordiator if block management is allowed
        elif self.session.can_manage(user, 'coordinate') and session_coordinator_priv_enabled(self.event_new,
                                                                                              'manage-blocks'):
            return True
        else:
            return False

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', _text=self.title or None)


SessionBlock.register_location_events()
