# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re
from collections import defaultdict

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.core.db.sqlalchemy.descriptions import RenderMode, RenderModeMixin
from indico.util.date_time import now_utc
from indico.util.enum import RichIntEnum
from indico.util.i18n import _
from indico.util.locators import locator_property
from indico.util.string import format_repr


class InitialRevisionState(RichIntEnum):
    __titles__ = [None, _('New'), _('Ready for Review'), _('Needs Confirmation')]
    __css_classes__ = [None, 'highlight', 'ready', 'warning']
    #: A revision that has been submitted by the user but isn't exposed to editors yet
    new = 1
    #: A revision that can be reviewed by editors
    ready_for_review = 2
    #: A revision with changes the submitter needs to approve or reject
    needs_submitter_confirmation = 3


class FinalRevisionState(RichIntEnum):
    __titles__ = [None, _('Replaced'), _('Needs Confirmation'), _('Needs Changes'), _('Accepted'), _('Rejected'),
                  _('Undone')]
    __css_classes__ = [None, 'highlight', 'warning', 'warning', 'success', 'error', None]
    #: A revision that is awaiting some action
    none = 0
    #: A revision that has been replaced by its next revision
    replaced = 1
    #: A revision that requires the submitter to confirm the next revision
    needs_submitter_confirmation = 2
    #: A revision that requires the submitter to submit a new revision
    needs_submitter_changes = 3
    #: A revision that has been accepted (no followup revision)
    accepted = 4
    #: A revision that has been rejected (no followup revision)
    rejected = 5
    #: A revision that has been undone
    undone = 6


def _make_state_check():
    return re.sub(r'\s+', ' ', '''
        (initial_state={i_new} AND final_state IN ({f_none}, {f_replaced})) OR
        (initial_state={i_ready_for_review}) OR
        (initial_state={i_needs_confirmation} AND
         (final_state IN ({f_none}, {f_needs_changes}, {f_accepted}, {f_undone})))
    '''.format(i_new=InitialRevisionState.new,
               i_ready_for_review=InitialRevisionState.ready_for_review,
               i_needs_confirmation=InitialRevisionState.needs_submitter_confirmation,
               f_none=FinalRevisionState.none,
               f_replaced=FinalRevisionState.replaced,
               f_needs_changes=FinalRevisionState.needs_submitter_changes,
               f_accepted=FinalRevisionState.accepted,
               f_undone=FinalRevisionState.undone)).strip()


def _make_reviewed_dt_check():
    return f'((final_state = {FinalRevisionState.none}) OR (reviewed_dt IS NOT NULL))'


class EditingRevision(RenderModeMixin, db.Model):
    __tablename__ = 'revisions'
    __table_args__ = (db.CheckConstraint(_make_state_check(), name='valid_state_combination'),
                      db.CheckConstraint(_make_reviewed_dt_check(), name='reviewed_dt_set_when_final_state'),
                      {'schema': 'event_editing'})

    possible_render_modes = {RenderMode.markdown}
    default_render_mode = RenderMode.markdown

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    editable_id = db.Column(
        db.ForeignKey('event_editing.editables.id'),
        index=True,
        nullable=False
    )
    submitter_id = db.Column(
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=False
    )
    editor_id = db.Column(
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=True
    )
    created_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc
    )
    reviewed_dt = db.Column(
        UTCDateTime,
        nullable=True
    )
    initial_state = db.Column(
        PyIntEnum(InitialRevisionState),
        nullable=False,
        default=InitialRevisionState.new
    )
    final_state = db.Column(
        PyIntEnum(FinalRevisionState),
        nullable=False,
        default=FinalRevisionState.none
    )
    _comment = db.Column(
        'comment',
        db.Text,
        nullable=False,
        default=''
    )

    editable = db.relationship(
        'Editable',
        foreign_keys=editable_id,
        lazy=True,
        backref=db.backref(
            'revisions',
            lazy=True,
            order_by=created_dt,
            cascade='all, delete-orphan'
        )
    )
    submitter = db.relationship(
        'User',
        lazy=True,
        foreign_keys=submitter_id,
        backref=db.backref(
            'editing_revisions',
            lazy='dynamic'
        )
    )
    editor = db.relationship(
        'User',
        lazy=True,
        foreign_keys=editor_id,
        backref=db.backref(
            'editor_for_revisions',
            lazy='dynamic'
        )
    )
    tags = db.relationship(
        'EditingTag',
        secondary='event_editing.revision_tags',
        collection_class=set,
        lazy=True,
        backref=db.backref(
            'revisions',
            collection_class=set,
            lazy=True
        )
    )

    #: A comment provided by whoever assigned the final state of the revision.
    comment = RenderModeMixin.create_hybrid_property('_comment')

    # relationship backrefs:
    # - comments (EditingRevisionComment.revision)
    # - files (EditingRevisionFile.revision)

    def __repr__(self):
        return format_repr(self, 'id', 'editable_id', 'initial_state', final_state=FinalRevisionState.none)

    @property
    def has_publishable_files(self):
        return any(file.file_type.publishable for file in self.files)

    @locator_property
    def locator(self):
        return dict(self.editable.locator, revision_id=self.id)

    def get_spotlight_file(self):
        files = [file for file in self.files if file.file_type.publishable]
        return files[0] if len(files) == 1 else None

    def get_published_files(self):
        """Get the published files, grouped by file type."""
        files = defaultdict(list)
        for file in self.files:
            if file.file_type.publishable:
                files[file.file_type].append(file)
        return dict(files)
