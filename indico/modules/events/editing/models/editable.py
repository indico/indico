# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.util.i18n import _
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii
from indico.util.struct.enum import RichIntEnum


class EditableType(RichIntEnum):
    __titles__ = [None, _('Paper'), _('Slides'), _('Poster')]
    __editor_permissions__ = [None, 'paper_editing', 'slides_editing', 'poster_editing']
    paper = 1
    slides = 2
    poster = 3

    @property
    def editor_permission(self):
        return self.__editor_permissions__[self]


class Editable(db.Model):
    __tablename__ = 'editables'
    __table_args__ = (db.UniqueConstraint('contribution_id', 'type'),
                      {'schema': 'event_editing'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    contribution_id = db.Column(
        db.ForeignKey('events.contributions.id'),
        index=True,
        nullable=False
    )
    type = db.Column(
        PyIntEnum(EditableType),
        nullable=False
    )
    editor_id = db.Column(
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=True
    )
    published_revision_id = db.Column(
        db.ForeignKey('event_editing.revisions.id'),
        index=True,
        nullable=True
    )

    contribution = db.relationship(
        'Contribution',
        lazy=True,
        backref=db.backref(
            'editables',
            lazy=True,
        )
    )
    editor = db.relationship(
        'User',
        lazy=True,
        backref=db.backref(
            'editor_for_editables',
            lazy='dynamic'
        )
    )
    published_revision = db.relationship(
        'EditingRevision',
        foreign_keys=published_revision_id,
        lazy=True,
    )

    # relationship backrefs:
    # - revisions (EditingRevision.editable)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'contribution_id', 'type')

    # TODO: state - either a column property referencing the newest revision's state or a normal column

    @locator_property
    def locator(self):
        return dict(self.contribution.locator, type=self.type.name)

    @property
    def event(self):
        return self.contribution.event

    def _has_general_editor_permissions(self, user):
        """Whether the user has general editor permissions on the Editable.

        This means that the user has editor permissions for the editable's type,
        but does not need to be the assigned editor.
        """
        # Editing (and event) managers always have editor-like access
        return (
            self.event.can_manage(user, permission='editing_manager') or
            self.event.can_manage(user, permission=self.type.editor_permission)
        )

    def can_see_timeline(self, user):
        """Whether the user can see the editable's timeline.

        This is pure read access, without any ability to make changes
        or leave comments.
        """
        # Anyone with editor access to the editable's type can see the timeline.
        # Users associated with the editable's contribution can do so as well.
        return (
            self._has_general_editor_permissions(user) or
            self.contribution.can_submit_proceedings(user) or
            self.contribution.is_user_associated(user, check_abstract=True)
        )

    def can_perform_submitter_actions(self, user):
        """Whether the user can perform any submitter actions.

        These are actions such as uploading a new revision after having
        been asked to make changes or approving/rejecting changes made
        by an editor.
        """
        # If the user can't even see the timeline, we never allow any modifications
        if not self.can_see_timeline(user):
            return False
        # Anyone who can submit new proceedings can also perform submitter actions,
        # i.e. the abstract submitter and anyone with submission access to the contribution.
        return self.contribution.can_submit_proceedings(user)

    def can_perform_editor_actions(self, user):
        """Whether the user can perform any Editing actions.

        These are actions usually made by the assigned Editor of the
        editable, such as making changes, asking the user to make changes,
        or approving/rejecting the editable.
        """
        from indico.modules.events.editing.settings import editable_type_settings

        # If the user can't even see the timeline, we never allow any modifications
        if not self.can_see_timeline(user):
            return False
        # Editing/event managers can perform actions without being the assigned editor
        # XXX: Do we want this? Or should they have to assign themselves first if they
        #      want to do actions that would usually be done by the assigned editor?
        if self.event.can_manage(user, permission='editing_manager'):
            return True
        # Editing needs to be enabled in the settings
        if not editable_type_settings[self.type].get(self.event, 'editing_enabled'):
            return False
        # Editors need the permission on the editable type and also be the assigned editor
        if self.editor == user and self.event.can_manage(user, permission=self.type.editor_permission):
            return True
        return False

    def can_use_internal_comments(self, user):
        """Whether the user can create/see internal comments."""
        return self._has_general_editor_permissions(user)

    def can_comment(self, user):
        """Whether the user can comment on the editable."""
        # We allow any user associated with the contribution to comment, even if they are
        # not authorized to actually perform submitter actions.
        return (self.event.can_manage(user, permission=self.type.editor_permission)
                or self.event.can_manage(user, permission='editing_manager')
                or self.contribution.is_user_associated(user, check_abstract=True))

    def can_assign_self(self, user):
        """Whether the user can assign themself on the editable."""
        from indico.modules.events.editing.settings import editable_type_settings
        return ((self.event.can_manage(user, permission=self.type.editor_permission)
                 and editable_type_settings[self.type].get(self.event, 'editing_enabled'))
                or self.event.can_manage(user, permission='editing_manager'))

    def can_unassign(self, user):
        """Whether the user can unassign the editor of the editable."""
        from indico.modules.events.editing.settings import editable_type_settings
        return (self.event.can_manage(user, permission='editing_manager')
                or (self.editor == user
                    and self.event.can_manage(user, permission=self.type.editor_permission)
                    and editable_type_settings[self.type].get(self.event, 'editing_enabled')))

    @property
    def review_conditions_valid(self):
        from indico.modules.events.editing.models.review_conditions import EditingReviewCondition
        query = EditingReviewCondition.query.with_parent(self.event).filter_by(type=self.type)
        review_conditions = [{ft.id for ft in cond.file_types} for cond in query]
        file_types = {file.file_type_id for file in self.revisions[-1].files}
        if not review_conditions:
            return True
        return any(file_types >= cond for cond in review_conditions)

    @property
    def editing_enabled(self):
        from indico.modules.events.editing.settings import editable_type_settings
        return editable_type_settings[self.type].get(self.event, 'editing_enabled')
