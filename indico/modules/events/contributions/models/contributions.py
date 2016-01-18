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

from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy.locations import LocationMixin
from indico.core.db.sqlalchemy.protection import ProtectionManagersMixin
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.core.db.sqlalchemy.util.queries import increment_and_get
from indico.modules.events.sessions.util import session_coordinator_priv_enabled
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii


def _get_next_friendly_id(context):
    """Get the next friendly id for a contribution."""
    from indico.modules.events import Event
    event_id = context.current_parameters['event_id']
    assert event_id is not None
    return increment_and_get(Event._last_friendly_contribution_id, Event.id == event_id)


class Contribution(ProtectionManagersMixin, LocationMixin, db.Model):
    __tablename__ = 'contributions'
    __auto_table_args = (db.Index(None, 'friendly_id', 'event_id', unique=True),
                         db.Index(None, 'event_id', 'track_id'),
                         db.Index(None, 'event_id', 'abstract_id'),
                         db.CheckConstraint("session_block_id IS NULL OR session_id IS NOT NULL",
                                            'session_block_if_session'),
                         db.ForeignKeyConstraint(['session_block_id', 'session_id'],
                                                 ['events.session_blocks.id', 'events.session_blocks.session_id']),
                         {'schema': 'events'})
    location_backref_name = 'contributions'
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
    session_id = db.Column(
        db.Integer,
        db.ForeignKey('events.sessions.id'),
        index=True,
        nullable=True
    )
    session_block_id = db.Column(
        db.Integer,
        db.ForeignKey('events.session_blocks.id'),
        index=True,
        nullable=True
    )
    track_id = db.Column(
        db.Integer,
        nullable=True
    )
    abstract_id = db.Column(
        db.Integer,
        nullable=True
    )
    type_id = db.Column(
        db.Integer,
        db.ForeignKey('events.contribution_types.id'),
        index=True,
        nullable=True
    )
    title = db.Column(
        db.String,
        nullable=False
    )
    description = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    duration = db.Column(
        db.Interval,
        nullable=False
    )
    board_number = db.Column(
        db.String,
        nullable=False,
        default=''
    )
    keywords = db.Column(
        ARRAY(db.String),
        nullable=False,
        default=[]
    )
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: The last user-friendly sub-contribution ID
    _last_friendly_subcontribution_id = db.deferred(db.Column(
        'last_friendly_subcontribution_id',
        db.Integer,
        nullable=False,
        default=0
    ))

    event_new = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'contributions',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )
    session = db.relationship(
        'Session',
        lazy=True,
        backref=db.backref(
            'contributions',
            lazy=True
        )
    )
    session_block = db.relationship(
        'SessionBlock',
        lazy=True,
        foreign_keys=[session_block_id],
        backref=db.backref(
            'contributions',
            lazy=True
        )
    )
    type = db.relationship(
        'ContributionType',
        lazy=True,
        backref=db.backref(
            'contributions',
            lazy=True
        )
    )
    acl_entries = db.relationship(
        'ContributionPrincipal',
        lazy=True,
        cascade='all, delete-orphan',
        collection_class=set,
        backref='contribution'
    )
    subcontributions = db.relationship(
        'SubContribution',
        lazy=True,
        order_by='SubContribution.position',
        cascade='all, delete-orphan',
        backref=db.backref(
            'contribution',
            lazy=True
        )
    )
    #: External references associated with this contribution
    references = db.relationship(
        'ContributionReference',
        lazy=True,
        cascade='all, delete-orphan',
        backref=db.backref(
            'contribution',
            lazy=True
        )
    )
    #: Persons associated with this contribution
    person_links = db.relationship(
        'ContributionPersonLink',
        lazy=True,
        cascade='all, delete-orphan',
        backref=db.backref(
            'contribution',
            lazy=True
        )
    )
    #: Data stored in abstract/contribution fields
    field_values = db.relationship(
        'ContributionFieldValue',
        lazy=True,
        cascade='all, delete-orphan',
        backref=db.backref(
            'contribution',
            lazy=True
        )
    )

    # relationship backrefs:
    # - legacy_mapping (LegacyContributionMapping.contribution)
    # - note (EventNote.contribution)
    # - timetable_entry (TimetableEntry.contribution)

    @property
    def location_parent(self):
        if self.session_block_id is not None:
            return self.session_block
        elif self.session_id is not None:
            return self.session
        else:
            return self.event_new

    @property
    def protection_parent(self):
        return self.session if self.session_id is not None else self.event_new

    @property
    def track(self):
        return self.event_new.as_legacy.getTrackById(str(self.track_id))

    @locator_property
    def locator(self):
        return dict(self.event_new.locator, contrib_id=self.id)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', _text=self.title)

    def can_manage(self, user, role=None, allow_admin=True, check_parent=True, explicit_role=False):
        if super(Contribution, self).can_manage(user, role, allow_admin=allow_admin, check_parent=check_parent,
                                                explicit_role=explicit_role):
            return True
        if (check_parent and self.session_id is not None and
                self.session.can_manage(user, 'coordinate', allow_admin=allow_admin, explicit_role=explicit_role) and
                session_coordinator_priv_enabled(self.event_new, 'manage-contributions')):
            return True
        return False
