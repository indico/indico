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
    #: A revision that requires the submitter to submit a new revision
    needs_submitter_changes = 5
    #: An editor revision that accepts the editable
    acceptance = 6
    #: An editor revision that rejects the editable
    rejection = 7
    #: An editor revision that undoes the previous revision
    undo = 8
    #: An editor revision that resets the state of the editable to "ready for review"
    reset = 9


class EditingRevision(RenderModeMixin, db.Model):
    __tablename__ = 'revisions'
    __table_args__ = (db.CheckConstraint(f'type IN ({RevisionType.new}, {RevisionType.ready_for_review}) OR revises_id IS NOT NULL', name='revises_set_unless_new'),
                      {'schema': 'event_editing'})
    # TODO revisions can only be revised by one not undone revision

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
    revises_id = db.Column(
        db.ForeignKey('event_editing.revisions.id'),
        index=True,
        nullable=True
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
                         '~EditingRevision.type.in_(({}, {}))').format(RevisionType.undo, RevisionType.reset),
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
    revises = db.relationship(
        'EditingRevision',
        lazy=True,
        remote_side=id,
        foreign_keys=revises_id,
        backref=db.backref(
            'revised_by',
            uselist=False,
            #primaryjoin='(EditingRevision.revises_id == EditingRevision.id) & ~EditingRevision.is_undone',
            #primaryjoin=(db.remote(revises_id) == id) & ~db.remote(is_undone),
            lazy=True
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

    @hybrid_property
    def is_replaced(self):
        return self.revised_by is not None and self.revised_by.type == RevisionType.ready_for_review

    @is_replaced.expression
    def is_replaced(cls):
        return cls.revised_by.has(type=RevisionType.ready_for_review)

    @hybrid_property
    def is_undone(self):
        return self.revised_by is not None and self.revised_by.type == RevisionType.undo

    @is_undone.expression
    def is_undone(cls):
        return cls.revised_by.has(type=RevisionType.undo)

    @hybrid_property
    def is_valid(self):
        #TODO make reset revisions invalid?
        return self.type != RevisionType.undo and not self.is_undone

    @is_valid.expression
    def is_valid(cls):
        return (cls.type != RevisionType.undo) & ~cls.is_undone

    @property
    def reviewed(self):
        return (self.is_valid and
                self.revised_by is not None and
                self.revised_by.is_valid and
                self.revised_by.type not in (RevisionType.new, RevisionType.ready_for_review))

    @property
    def is_editor(self):
        if self.type in (RevisionType.needs_submitter_confirmation, RevisionType.acceptance, RevisionType.rejection,
                         RevisionType.undo, RevisionType.reset):
            return True
        if (self.type == RevisionType.needs_submitter_changes and
                self.revises.type != RevisionType.needs_submitter_confirmation):
            return True
        return False
