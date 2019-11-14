# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import request, session
from marshmallow import fields
from marshmallow_enum import EnumField
from werkzeug.exceptions import Forbidden, NotFound

from indico.core.errors import UserValueError
from indico.modules.events.contributions.controllers.display import RHContributionDisplayBase
from indico.modules.events.controllers.base import RHEventBase
from indico.modules.events.editing.fields import EditingFilesField, EditingTagsField
from indico.modules.events.editing.models.editable import Editable, EditableType
from indico.modules.events.editing.models.revisions import FinalRevisionState, InitialRevisionState
from indico.modules.events.editing.operations import (confirm_editable_changes, create_new_editable, replace_revision,
                                                      review_editable_revision)
from indico.modules.events.editing.schemas import (EditableSchema, EditingConfirmationAction, EditingFileTypeSchema,
                                                   EditingReviewAction, EditingTagSchema, ReviewEditableArgs)
from indico.util.i18n import _
from indico.web.args import parser, use_kwargs


class RHEditingFileTypes(RHEventBase):
    """Return all editing file types defined in the event."""

    def _process(self):
        return EditingFileTypeSchema(many=True).jsonify(self.event.editing_file_types)


class RHEditingTags(RHEventBase):
    """Return all editing tags defined in the event."""

    def _process(self):
        return EditingTagSchema(many=True).jsonify(self.event.editing_tags)


class RHContributionEditableBase(RHContributionDisplayBase):
    """Base class for operations on an editable."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.contrib
        },
        'preserved_args': {'type'}
    }

    def _process_args(self):
        RHContributionDisplayBase._process_args(self)
        self.editable = (Editable.query
                         .with_parent(self.contrib)
                         .filter_by(type=EditableType[request.view_args['type']])
                         .first())

    def _check_access(self):
        RHContributionDisplayBase._check_access(self)
        if not session.user:
            raise Forbidden

    def _user_is_authorized_submitter(self):
        if session.user.is_admin:
            # XXX: not sure if we want to keep this, but for now it's useful to have!
            return True
        return self.contrib.is_user_associated(session.user, check_abstract=True)

    def _user_is_authorized_editor(self):
        if session.user.is_admin:
            # XXX: not sure if we want to keep this, but for now it's useful to have!
            return True
        return self.editable.editor == session.user


class RHContributionEditableRevisionBase(RHContributionEditableBase):
    """Base class for operations on the latest revision of an Editable."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.contrib
        },
        'preserved_args': {'type', 'revision_id'}
    }

    def _process_args(self):
        RHContributionEditableBase._process_args(self)
        if not self.editable:
            raise NotFound
        self.revision = self.editable.revisions[-1]
        if self.revision.id != request.view_args['revision_id']:
            raise UserValueError(_('Only the latest revision can be updated'))

    def _check_revision_access(self):
        raise NotImplementedError

    def _check_access(self):
        RHContributionEditableBase._check_access(self)
        if not self._check_revision_access():
            raise UserValueError(_('You cannot perform this action on this revision'))


class RHEditable(RHContributionEditableBase):
    """Retrieve an Editable with all its data."""

    def _check_access(self):
        RHContributionEditableBase._check_access(self)
        if self.event.can_manage(session.user):
            return
        if not self._user_is_authorized_editor() and not self._user_is_authorized_editor():
            raise Forbidden

    def _process(self):
        return EditableSchema().jsonify(self.editable)


class RHCreateEditable(RHContributionEditableBase):
    """Create a new Editable for a contribution."""

    def _check_access(self):
        RHContributionEditableBase._check_access(self)
        if not self._user_is_authorized_submitter():
            # XXX: should event managers be able to submit on behalf of the user?
            raise Forbidden
        # TODO: check if submitting papers for editing is allowed in the event

    def _process(self):
        if self.editable:
            raise UserValueError('Editable already exists')

        args = parser.parse({
            'files': EditingFilesField(self.event, required=True)
        })

        create_new_editable(self.contrib, EditableType[request.view_args['type']], session.user, args['files'])
        return '', 201


class RHReviewEditable(RHContributionEditableRevisionBase):
    """Review the latest revision of an Editable."""

    def _check_revision_access(self):
        if not self._user_is_authorized_editor():
            return False
        if self.revision.initial_state != InitialRevisionState.ready_for_review:
            return False
        return self.revision.final_state == FinalRevisionState.none

    @use_kwargs(ReviewEditableArgs())
    def _process(self, action, comment):
        argmap = {'tags': EditingTagsField(self.event, missing=set())}
        if action == EditingReviewAction.update:
            argmap['files'] = EditingFilesField(self.event, allow_claimed_files=True, required=True)
        args = parser.parse(argmap)
        review_editable_revision(self.revision, session.user, action, comment, args['tags'], args.get('files'))
        return '', 204


class RHConfirmEditableChanges(RHContributionEditableRevisionBase):
    """Confirm/reject the changes made by the editor on an Editable."""

    def _check_revision_access(self):
        if not self._user_is_authorized_submitter():
            return False
        if self.revision.final_state != FinalRevisionState.none:
            return False
        return self.revision.initial_state == InitialRevisionState.needs_submitter_confirmation

    @use_kwargs({
        'action': EnumField(EditingConfirmationAction, required=True),
        'comment': fields.String(missing='')
    })
    def _process(self, action, comment):
        confirm_editable_changes(self.revision, session.user, action, comment)
        return '', 204


class RHReplaceRevision(RHContributionEditableRevisionBase):
    """Replace the latest revision of an Editable."""

    def _check_revision_access(self):
        if self.revision.editor is not None:
            return False
        if self.revision.initial_state not in (InitialRevisionState.new, InitialRevisionState.ready_for_review):
            return False
        return self.revision.final_state == FinalRevisionState.none

    @use_kwargs({
        'comment': fields.String(missing='')
    })
    def _process(self, comment):
        args = parser.parse({
            'files': EditingFilesField(self.event, allow_claimed_files=True, required=True)
        })

        replace_revision(self.revision, session.user, comment, args['files'])
        return '', 204
