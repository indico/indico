# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from functools import partial

from flask import g
from sqlalchemy.event import listen, listens_for
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.core.db.sqlalchemy.descriptions import RenderMode
from indico.core.db.sqlalchemy.links import LinkMixin, LinkType
from indico.core.db.sqlalchemy.searchable import fts_matches, make_fts_index
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.notes.util import render_note
from indico.util.date_time import now_utc
from indico.util.decorators import strict_classproperty
from indico.util.locators import locator_property
from indico.util.string import text_to_repr


class EventNote(LinkMixin, db.Model):
    __tablename__ = 'notes'
    allowed_link_types = LinkMixin.allowed_link_types - {LinkType.category, LinkType.session_block}
    unique_links = True
    events_backref_name = 'all_notes'
    link_backref_name = 'note'

    @strict_classproperty
    @classmethod
    def __auto_table_args(cls):
        return (make_fts_index(cls, 'html'),
                {'schema': 'events'})

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls)

    #: The ID of the note
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: If the note has been deleted
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: The rendered HTML of the note
    html = db.Column(
        db.Text,
        nullable=False
    )
    #: The ID of the current revision
    current_revision_id = db.Column(
        db.Integer,
        db.ForeignKey('events.note_revisions.id', use_alter=True),
        nullable=True  # needed for post_update :(
    )

    #: The list of all revisions for the note
    revisions = db.relationship(
        'EventNoteRevision',
        primaryjoin=lambda: EventNote.id == EventNoteRevision.note_id,
        foreign_keys=lambda: EventNoteRevision.note_id,
        lazy=True,
        cascade='all, delete-orphan',
        order_by=lambda: EventNoteRevision.created_dt.desc(),
        backref=db.backref(
            'note',
            lazy=False
        )
    )
    #: The currently active revision of the note
    current_revision = db.relationship(
        'EventNoteRevision',
        primaryjoin=lambda: EventNote.current_revision_id == EventNoteRevision.id,
        foreign_keys=current_revision_id,
        lazy=True,
        post_update=True
    )

    @locator_property
    def locator(self):
        return self.object.locator

    @classmethod
    def get_for_linked_object(cls, linked_object, preload_event=True):
        """Get the note for the given object.

        This only returns a note that hasn't been deleted.

        :param linked_object: An event, session, contribution or
                              subcontribution.
        :param preload_event: If all notes for the same event should
                              be pre-loaded and cached in the app
                              context.
        """
        event = linked_object.event
        try:
            return g.event_notes[event].get(linked_object)
        except (AttributeError, KeyError):
            if not preload_event:
                return linked_object.note if linked_object.note and not linked_object.note.is_deleted else None
            if 'event_notes' not in g:
                g.event_notes = {}
            query = (event.all_notes
                     .filter_by(is_deleted=False)
                     .options(joinedload(EventNote.linked_event),
                              joinedload(EventNote.session),
                              joinedload(EventNote.contribution),
                              joinedload(EventNote.subcontribution)))
            g.event_notes[event] = {n.object: n for n in query}
            return g.event_notes[event].get(linked_object)

    @classmethod
    def get_or_create(cls, linked_object):
        """Get the note for the given object or creates a new one.

        If there is an existing note for the object, it will be returned
        even.  Otherwise a new note is created.
        """
        note = cls.query.filter_by(object=linked_object).first()
        if note is None:
            note = cls(object=linked_object)
        return note

    def delete(self, user):
        """Mark the note as deleted and adds a new empty revision."""
        self.create_revision(self.current_revision.render_mode, '', user)
        self.is_deleted = True

    def create_revision(self, render_mode, source, user):
        """Create a new revision if needed and marks it as undeleted if it was.

        Any change to the render mode or the source causes a new
        revision to be created.  The user is not taken into account
        since a user "modifying" a note without changing things is
        not really a change.
        """
        self.is_deleted = False
        with db.session.no_autoflush:
            current = self.current_revision
        if current is not None and current.render_mode == render_mode and current.source == source:
            return current
        self.current_revision = EventNoteRevision(render_mode=render_mode, source=source, user=user)
        return self.current_revision

    @classmethod
    def html_matches(cls, search_string, exact=False):
        """Check whether the html content matches a search string.

        To be used in a SQLAlchemy `filter` call.

        :param search_string: A string to search for
        :param exact: Whether to search for the exact string
        """
        return fts_matches(cls.html, search_string, exact=exact)

    def __repr__(self):
        return '<EventNote({}, current_revision={}{}, {})>'.format(
            self.id,
            self.current_revision_id,
            ', is_deleted=True' if self.is_deleted else '',
            self.link_repr
        )


class EventNoteRevision(db.Model):
    __tablename__ = 'note_revisions'
    __table_args__ = {'schema': 'events'}

    #: The ID of the revision
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the associated note
    note_id = db.Column(
        db.Integer,
        db.ForeignKey('events.notes.id'),
        nullable=False,
        index=True
    )
    #: The user who created the revision
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        nullable=False,
        index=True
    )
    #: The date/time when the revision was created
    created_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc
    )
    #: How the note is rendered
    render_mode = db.Column(
        PyIntEnum(RenderMode),
        nullable=False
    )
    #: The raw source of the note as provided by the user
    source = db.Column(
        db.Text,
        nullable=False
    )
    #: The rendered HTML of the note
    html = db.Column(
        db.Text,
        nullable=False
    )

    #: The user who created the revision
    user = db.relationship(
        'User',
        lazy=True,
        backref=db.backref(
            'event_notes_revisions',
            lazy='dynamic'
        )
    )

    # relationship backrefs:
    # - note (EventNote.revisions)

    def __repr__(self):
        render_mode = self.render_mode.name if self.render_mode is not None else None
        source = text_to_repr(self.source, html=True)
        return f'<EventNoteRevision({self.id}, {self.note_id}, {render_mode}, {self.created_dt}): "{source}">'


@listens_for(EventNote.current_revision, 'set')
def _add_current_revision(target, value, *unused):
    if value is None:
        raise ValueError('current_revision cannot be set to None')
    with db.session.no_autoflush:
        target.revisions.append(value)
    target.html = value.html


@no_autoflush
def _render_revision(attr, target, value, *unused):
    source = value if attr == 'source' else target.source
    render_mode = value if attr == 'render_mode' else target.render_mode
    if source is None or render_mode is None:
        return

    target.html = render_note(source, render_mode)


listen(EventNoteRevision.render_mode, 'set', partial(_render_revision, 'render_mode'))
listen(EventNoteRevision.source, 'set', partial(_render_revision, 'source'))


@listens_for(EventNoteRevision.html, 'set')
def _update_note_html(target, value, *unused):
    if target.note_id is not None and target == target.note.current_revision:
        target.note.html = value


EventNote.register_link_events()
