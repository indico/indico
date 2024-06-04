# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from collections import defaultdict

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.core.db.sqlalchemy.descriptions import RenderMode, RenderModeMixin
from indico.util.date_time import now_utc
from indico.util.enum import IndicoIntEnum
from indico.util.locators import locator_property
from indico.util.string import format_repr


class RevisionType(IndicoIntEnum):
    #: A submitter revision that hasn't been exposed to editors yet
    new = 1
    #: A submitter revision that can be reviewed by editors
    ready_for_review = 2
    #: An editor revision with changes the submitter needs to approve or reject
    needs_submitter_confirmation = 3
    #: A submitter revision that accepts the changes made by the editor
    changes_acceptance = 4
    #: A submitter revision that rejects the changes made by the editor
    changes_rejection = 5
    #: An editor revision that requires the submitter to submit a new revision
    needs_submitter_changes = 6
    #: An editor revision that accepts the editable
    acceptance = 7
    #: An editor revision that rejects the editable
    rejection = 8
    #: A system revision that replaces the current revision
    replacement = 9
    #: A system revision that resets the state of the editable to "ready for review"
    reset = 10

    @property
    def is_submitter_action(self):
        return self in (
            RevisionType.new,
            RevisionType.ready_for_review,
            RevisionType.changes_acceptance,
            RevisionType.changes_rejection
        )

    @property
    def is_editor_action(self):
        return self in (
            RevisionType.needs_submitter_confirmation,
            RevisionType.acceptance,
            RevisionType.rejection,
            RevisionType.reset,
            RevisionType.needs_submitter_changes
        )


class EditingRevision(RenderModeMixin, db.Model):
    __tablename__ = 'revisions'
    __table_args__ = (db.CheckConstraint(f'type != {RevisionType.new} OR NOT is_undone',
                                         name='new_revision_not_undone'),
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
    user_id = db.Column(
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=False
    )
    created_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc
    )
    modified_dt = db.Column(
        UTCDateTime,
        nullable=True
    )
    type = db.Column(
        PyIntEnum(RevisionType),
        nullable=False,
        default=RevisionType.new
    )
    is_undone = db.Column(
        db.Boolean,
        nullable=False,
        default=False
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
    user = db.relationship(
        'User',
        lazy=True,
        foreign_keys=user_id,
        backref=db.backref(
            'editing_revisions',
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

    #: A comment provided by whoever made the revision.
    comment = RenderModeMixin.create_hybrid_property('_comment')

    # relationship backrefs:
    # - comments (EditingRevisionComment.revision)
    # - files (EditingRevisionFile.revision)

    def __repr__(self):
        return format_repr(self, 'id', 'editable_id', 'type')

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

    @property
    def is_submitter_revision(self):
        return self.type.is_submitter_action

    @property
    def is_editor_revision(self):
        return self.type.is_editor_action
