# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from datetime import timedelta
from operator import attrgetter

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy.attachments import AttachedItemsMixin
from indico.core.db.sqlalchemy.colors import ColorMixin, ColorTuple
from indico.core.db.sqlalchemy.descriptions import DescriptionMixin, RenderMode
from indico.core.db.sqlalchemy.locations import LocationMixin
from indico.core.db.sqlalchemy.notes import AttachedNotesMixin
from indico.core.db.sqlalchemy.protection import ProtectionManagersMixin
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.core.db.sqlalchemy.util.queries import increment_and_get
from indico.modules.events.management.util import get_non_inheriting_objects
from indico.modules.events.timetable.models.entries import TimetableEntry, TimetableEntryType
from indico.util.caching import memoize_request
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii


def _get_next_friendly_id(context):
    """Get the next friendly id for a session."""
    from indico.modules.events import Event
    event_id = context.current_parameters['event_id']
    assert event_id is not None
    return increment_and_get(Event._last_friendly_session_id, Event.id == event_id)


class Session(DescriptionMixin, ColorMixin, ProtectionManagersMixin, LocationMixin, AttachedItemsMixin,
              AttachedNotesMixin, db.Model):
    __tablename__ = 'sessions'
    __auto_table_args = (db.Index(None, 'friendly_id', 'event_id', unique=True,
                                  postgresql_where=db.text('NOT is_deleted')),
                         {'schema': 'events'})
    location_backref_name = 'sessions'
    disallowed_protection_modes = frozenset()
    inheriting_have_acl = True
    default_colors = ColorTuple('#202020', '#e3f2d3')
    allow_relationship_preloading = True

    PRELOAD_EVENT_ATTACHED_ITEMS = True
    PRELOAD_EVENT_NOTES = True
    ATTACHMENT_FOLDER_ID_COLUMN = 'session_id'
    possible_render_modes = {RenderMode.markdown}
    default_render_mode = RenderMode.markdown

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls)

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The human-friendly ID for the session
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
    type_id = db.Column(
        db.Integer,
        db.ForeignKey('events.session_types.id'),
        index=True,
        nullable=True
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
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    event = db.relationship(
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
    type = db.relationship(
        'SessionType',
        lazy=True,
        backref=db.backref(
            'sessions',
            lazy=True
        )
    )

    # relationship backrefs:
    # - attachment_folders (AttachmentFolder.session)
    # - contributions (Contribution.session)
    # - default_for_tracks (Track.default_session)
    # - legacy_mapping (LegacySessionMapping.session)
    # - note (EventNote.session)

    def __init__(self, **kwargs):
        # explicitly initialize this relationship with None to avoid
        # an extra query to check whether there is an object associated
        # when assigning a new one (e.g. during cloning)
        kwargs.setdefault('note', None)
        super(Session, self).__init__(**kwargs)

    @classmethod
    def preload_acl_entries(cls, event):
        cls.preload_relationships(cls.query.with_parent(event), 'acl_entries')

    @property
    def location_parent(self):
        return self.event

    @property
    def protection_parent(self):
        return self.event

    @property
    def session(self):
        """Convenience property so all event entities have it."""
        return self

    @property
    @memoize_request
    def start_dt(self):
        from indico.modules.events.sessions.models.blocks import SessionBlock
        start_dt = (self.event.timetable_entries
                    .with_entities(TimetableEntry.start_dt)
                    .join('session_block')
                    .filter(TimetableEntry.type == TimetableEntryType.SESSION_BLOCK,
                            SessionBlock.session == self)
                    .order_by(TimetableEntry.start_dt)
                    .first())
        return start_dt[0] if start_dt else None

    @property
    @memoize_request
    def end_dt(self):
        sorted_blocks = sorted(self.blocks, key=attrgetter('timetable_entry.end_dt'), reverse=True)
        return sorted_blocks[0].timetable_entry.end_dt if sorted_blocks else None

    @property
    @memoize_request
    def conveners(self):
        from indico.modules.events.sessions.models.blocks import SessionBlock
        from indico.modules.events.sessions.models.persons import SessionBlockPersonLink

        return (SessionBlockPersonLink.query
                .join(SessionBlock)
                .filter(SessionBlock.session_id == self.id)
                .distinct(SessionBlockPersonLink.person_id)
                .all())

    @property
    def is_poster(self):
        return self.type.is_poster if self.type else False

    @locator_property
    def locator(self):
        return dict(self.event.locator, session_id=self.id)

    def get_non_inheriting_objects(self):
        """Get a set of child objects that do not inherit protection."""
        return get_non_inheriting_objects(self)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', is_deleted=False, _text=self.title)

    def can_manage_contributions(self, user, allow_admin=True):
        """Check whether a user can manage contributions within the session."""
        from indico.modules.events.sessions.util import session_coordinator_priv_enabled
        if user is None:
            return False
        elif self.session.can_manage(user, allow_admin=allow_admin):
            return True
        elif (self.session.can_manage(user, 'coordinate') and
                session_coordinator_priv_enabled(self.event, 'manage-contributions')):
            return True
        else:
            return False

    def can_manage_blocks(self, user, allow_admin=True):
        """Check whether a user can manage session blocks.

        This only applies to the blocks themselves, not to contributions inside them.
        """
        from indico.modules.events.sessions.util import session_coordinator_priv_enabled
        if user is None:
            return False
        # full session manager can always manage blocks. this also includes event managers and higher.
        elif self.session.can_manage(user, allow_admin=allow_admin):
            return True
        # session coordiator if block management is allowed
        elif (self.session.can_manage(user, 'coordinate') and
                session_coordinator_priv_enabled(self.event, 'manage-blocks')):
            return True
        else:
            return False


Session.register_location_events()
Session.register_protection_events()
