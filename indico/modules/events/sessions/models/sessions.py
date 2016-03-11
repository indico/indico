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

from datetime import timedelta

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy.attachments import AttachedItemsMixin
from indico.core.db.sqlalchemy.colors import ColorMixin, ColorTuple
from indico.core.db.sqlalchemy.descriptions import DescriptionMixin
from indico.core.db.sqlalchemy.locations import LocationMixin
from indico.core.db.sqlalchemy.notes import AttachedNotesMixin
from indico.core.db.sqlalchemy.protection import ProtectionManagersMixin
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.core.db.sqlalchemy.util.queries import increment_and_get
from indico.modules.events.management.util import get_non_inheriting_objects
from indico.modules.attachments.util import can_manage_attachments
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii


def _get_next_friendly_id(context):
    """Get the next friendly id for a contribution."""
    from indico.modules.events import Event
    event_id = context.current_parameters['event_id']
    assert event_id is not None
    return increment_and_get(Event._last_friendly_session_id, Event.id == event_id)


class Session(DescriptionMixin, ColorMixin, ProtectionManagersMixin, LocationMixin, AttachedItemsMixin,
              AttachedNotesMixin, db.Model):
    __tablename__ = 'sessions'
    __auto_table_args = {'schema': 'events'}
    location_backref_name = 'sessions'
    disallowed_protection_modes = frozenset()
    default_colors = ColorTuple('#202020', '#e3f2d3')

    PRELOAD_EVENT_ATTACHED_ITEMS = True
    PRELOAD_EVENT_ATTACHED_NOTES = True
    ATTACHMENT_FOLDER_ID_COLUMN = 'session_id'

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
    code = db.Column(
        db.String,
        nullable=False,
        default=''
    )
    default_contribution_duration = db.Column(
        db.Interval,
        nullable=False,
        default=timedelta(minutes=20)
    )
    is_poster = db.Column(
        db.Boolean,
        nullable=False,
        default=False
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
            primaryjoin='(Session.event_id == Event.id) & ~Session.is_deleted',
            cascade='all, delete-orphan',
            lazy=True
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
    # - attachment_folders (AttachmentFolder.session)
    # - contributions (Contribution.session)
    # - legacy_mapping (LegacySessionMapping.session)
    # - note (EventNote.session)

    def __init__(self, **kwargs):
        # explicitly initialize this relationship with None to avoid
        # an extra query to check whether there is an object associated
        # when assigning a new one (e.g. during cloning)
        kwargs.setdefault('note', None)
        super(Session, self).__init__(**kwargs)

    @property
    def location_parent(self):
        return self.event_new

    @property
    def protection_parent(self):
        return self.event_new

    def can_manage_attachments(self, user):
        return can_manage_attachments(self, user)

    @property
    def session(self):
        """Convenience property so all event entities have it"""
        return self

    @locator_property
    def locator(self):
        return dict(self.event_new.locator, session_id=self.id)

    def get_non_inheriting_objects(self):
        """Get a set of child objects that do not inherit protection"""
        return get_non_inheriting_objects(self)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', is_poster=False, is_deleted=False, _text=self.title)


Session.register_location_events()
