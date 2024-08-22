# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session
from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy.attachments import AttachedItemsMixin
from indico.core.db.sqlalchemy.descriptions import RenderMode, SearchableDescriptionMixin
from indico.core.db.sqlalchemy.notes import AttachedNotesMixin
from indico.core.db.sqlalchemy.searchable import SearchableTitleMixin
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.core.db.sqlalchemy.util.queries import increment_and_get
from indico.util.iterables import materialize_iterable
from indico.util.locators import locator_property
from indico.util.string import format_repr, slugify


def _get_next_friendly_id(context):
    """Get the next friendly id for a sub-contribution."""
    from indico.modules.events.contributions.models.contributions import Contribution
    contribution_id = context.current_parameters['contribution_id']
    assert contribution_id is not None
    return increment_and_get(Contribution._last_friendly_subcontribution_id, Contribution.id == contribution_id)


def _get_next_position(context):
    """Get the next menu entry position for the event."""
    contribution_id = context.current_parameters['contribution_id']
    res = (db.session.query(db.func.max(SubContribution.position))
           .filter(SubContribution.contribution_id == contribution_id)
           .one())
    return (res[0] or 0) + 1


class SubContribution(SearchableTitleMixin, SearchableDescriptionMixin, AttachedItemsMixin, AttachedNotesMixin,
                      db.Model):
    __tablename__ = 'subcontributions'
    __auto_table_args = (db.Index(None, 'friendly_id', 'contribution_id', unique=True),
                         db.CheckConstraint("date_trunc('minute', duration) = duration", 'duration_no_seconds'),
                         db.CheckConstraint("duration >= '0'", 'nonnegative_duration'),
                         {'schema': 'events'})

    PRELOAD_EVENT_ATTACHED_ITEMS = True
    PRELOAD_EVENT_NOTES = True
    ATTACHMENT_FOLDER_ID_COLUMN = 'subcontribution_id'
    possible_render_modes = {RenderMode.html, RenderMode.markdown}
    default_render_mode = RenderMode.markdown

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls)

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The human-friendly ID for the sub-contribution
    friendly_id = db.Column(
        db.Integer,
        nullable=False,
        default=_get_next_friendly_id
    )
    contribution_id = db.Column(
        db.Integer,
        db.ForeignKey('events.contributions.id'),
        index=True,
        nullable=False
    )
    position = db.Column(
        db.Integer,
        nullable=False,
        default=_get_next_position
    )
    code = db.Column(
        db.String,
        nullable=False,
        default=''
    )
    duration = db.Column(
        db.Interval,
        nullable=False
    )
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    #: External references associated with this contribution
    references = db.relationship(
        'SubContributionReference',
        lazy=True,
        cascade='all, delete-orphan',
        backref=db.backref(
            'subcontribution',
            lazy=True
        )
    )
    #: Persons associated with this contribution
    person_links = db.relationship(
        'SubContributionPersonLink',
        lazy=True,
        cascade='all, delete-orphan',
        backref=db.backref(
            'subcontribution',
            lazy=True
        )
    )

    # relationship backrefs:
    # - attachment_folders (AttachmentFolder.subcontribution)
    # - contribution (Contribution.subcontributions)
    # - legacy_mapping (LegacySubContributionMapping.subcontribution)
    # - note (EventNote.subcontribution)

    def __init__(self, **kwargs):
        # explicitly initialize this relationship with None to avoid
        # an extra query to check whether there is an object associated
        # when assigning a new one (e.g. during cloning)
        kwargs.setdefault('note', None)
        super().__init__(**kwargs)

    @property
    def event(self):
        return self.contribution.event

    @locator_property
    def locator(self):
        return dict(self.contribution.locator, subcontrib_id=self.id)

    @property
    def is_protected(self):
        return self.contribution.is_protected

    @property
    def session(self):
        """Convenience property so all event entities have it."""
        return self.contribution.session if self.contribution.session_id is not None else None

    @property
    def timetable_entry(self):
        """Convenience property so all event entities have it."""
        return self.contribution.timetable_entry

    @property
    def speakers(self):
        return self.person_links

    @speakers.setter
    def speakers(self, value):
        self.person_links = list(value.keys())

    @property
    def slug(self):
        return slugify('sc', self.contribution.friendly_id, self.friendly_id, self.title, maxlen=30)

    @property
    def location_parent(self):
        return self.contribution

    @property
    def venue_name(self):
        return self.location_parent.venue_name

    @property
    def room_name(self):
        return self.location_parent.room_name

    def get_access_list(self):
        return self.contribution.get_access_list()

    def get_manager_list(self, recursive=False, include_groups=True):
        return self.contribution.get_manager_list(recursive=recursive, include_groups=include_groups)

    def __repr__(self):
        return format_repr(self, 'id', is_deleted=False, _text=self.title)

    def can_access(self, user, **kwargs):
        return self.contribution.can_access(user, **kwargs)

    def can_manage(self, user, permission=None, **kwargs):
        return self.contribution.can_manage(user, permission=permission, **kwargs)

    def can_edit(self, user):
        return self.contribution.can_edit(user)

    @materialize_iterable()
    def get_manage_button_options(self, *, note_may_exist=False):
        if self.event.is_locked:
            return
        if self.can_edit_note(session.user) and (note_may_exist or not self.has_note):
            yield 'notes_edit'
        if self.can_edit(session.user):
            yield 'subcontribution_edit'
        if self.can_manage_attachments(session.user):
            yield 'attachments_edit'

    def is_user_associated(self, user):
        if user is None:
            return False
        if self.contribution.is_user_associated(user):
            return True
        return any(pl.person.user == user for pl in self.person_links if pl.person.user)
