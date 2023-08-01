# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from collections import defaultdict

from sqlalchemy.ext.hybrid import hybrid_property

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.core.db.sqlalchemy.descriptions import RenderMode, RenderModeMixin
from indico.util.date_time import now_utc
from indico.util.enum import RichIntEnum
from indico.util.i18n import _
from indico.util.locators import locator_property
from indico.util.string import format_repr


class RevisionType(RichIntEnum):
    __titles__ = [None, _('New'), _('Ready for Review'), _('Needs Confirmation'), _('Accepted'), _('Needs Changes'),
                  _('Accepted'), _('Rejected'), _('Undone'), _('Reset')]
    __css_classes__ = [None, 'highlight', 'ready', 'warning', 'success', 'warning', 'success', 'error', None, None]
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
    #: An editor revision that resets the state of the editable to "ready for review"
    reset = 9


class EditingRevision(RenderModeMixin, db.Model):
    __tablename__ = 'revisions'
    __table_args__ = (db.CheckConstraint(f'type != {RevisionType.new} OR is_undone = false', #TODO consider adding r4r as well
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
            primaryjoin=('(EditingRevision.editable_id == Editable.id) & '
                         f'(EditingRevision.type != {RevisionType.reset})'),
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
    def is_editor(self):
        if self.type in (RevisionType.needs_submitter_confirmation, RevisionType.acceptance,
                         RevisionType.rejection, RevisionType.reset, RevisionType.needs_submitter_changes):
            return True
        return False
