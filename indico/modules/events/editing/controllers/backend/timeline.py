# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
import shutil
from io import BytesIO
from operator import attrgetter
from zipfile import ZipFile, ZipInfo

from flask import jsonify, request, session
from marshmallow import EXCLUDE, fields
from marshmallow_enum import EnumField
from sqlalchemy.orm import joinedload
from werkzeug.exceptions import BadRequest, Conflict, Forbidden, NotFound, ServiceUnavailable

from indico.core.errors import NoReportError, UserValueError
from indico.modules.events.editing.controllers.backend.util import (confirm_and_publish_changes,
                                                                    review_and_publish_editable)
from indico.modules.events.editing.controllers.base import RHContributionEditableBase, TokenAccessMixin
from indico.modules.events.editing.fields import EditingFilesField, EditingTagsField
from indico.modules.events.editing.models.comments import EditingRevisionComment
from indico.modules.events.editing.models.revision_files import EditingRevisionFile
from indico.modules.events.editing.models.revisions import EditingRevision, RevisionType
from indico.modules.events.editing.operations import (assign_editor, create_new_editable, create_revision_comment,
                                                      create_submitter_revision, delete_editable,
                                                      delete_revision_comment, ensure_latest_revision, replace_revision,
                                                      unassign_editor, undo_review, update_review_comment,
                                                      update_revision_comment)
from indico.modules.events.editing.schemas import (EditableSchema, EditingConfirmationAction, EditingReviewAction,
                                                   ReviewEditableArgs)
from indico.modules.events.editing.service import (ServiceRequestFailed, service_get_custom_actions,
                                                   service_handle_custom_action, service_handle_delete_editable,
                                                   service_handle_new_editable, service_handle_review_editable)
from indico.modules.events.editing.settings import editing_settings
from indico.modules.files.controllers import UploadFileMixin
from indico.modules.users import User
from indico.util.fs import secure_filename
from indico.util.i18n import _
from indico.util.marshmallow import not_empty
from indico.web.args import parser, use_kwargs
from indico.web.flask.util import send_file


class RHEditingUploadFile(UploadFileMixin, RHContributionEditableBase):
    SERVICE_ALLOWED = True
    EDITABLE_REQUIRED = False

    def get_file_context(self):
        return 'event', self.event.id, 'editing', self.contrib.id, self.editable_type.name


class RHEditingUploadContributionFile(RHEditingUploadFile):
    @use_kwargs({
        'id': fields.Int(load_default=None),
        'paper_id': fields.Int(load_default=None)
    })
    def _process(self, id, paper_id):
        if bool(id) == bool(paper_id):
            raise BadRequest
        files = []
        if id and self.contrib.editables:
            files = [file.file for e in self.contrib.editables
                     if e.type == self.editable.type for file in e.revisions[-1].files]
        if paper_id and self.contrib.paper and (last_rev := self.contrib.paper.get_last_revision()):
            files = last_rev.files
        if found := next((f for f in files if f.id == (id or paper_id)), None):
            with found.open() as stream:
                return self._save_file(found, stream)
        raise UserValueError(_('No such file was found within the paper'))


class RHContributionEditableRevisionBase(RHContributionEditableBase):
    """Base class for operations on the latest revision of an Editable."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.revision
        }
    }

    def _process_args(self):
        RHContributionEditableBase._process_args(self)
        if not self.editable:
            raise NotFound
        self.revision = (EditingRevision.query
                         .with_parent(self.editable, 'revisions')
                         .filter_by(id=request.view_args['revision_id'])
                         .first_or_404())

        if self.revision is None:
            raise NotFound

    def _check_revision_access(self):
        raise NotImplementedError

    def _check_access(self):
        if not TokenAccessMixin._token_can_access(self):
            RHContributionEditableBase._check_access(self)
            if not self._check_revision_access():
                raise UserValueError(_('You cannot perform this action on this revision'))


class RHEditable(RHContributionEditableBase):
    """Retrieve an Editable with all its data."""

    @property
    def _editable_query_options(self):
        revisions_strategy = joinedload('revisions')
        revisions_strategy.selectinload('comments').joinedload('user')
        revisions_strategy.selectinload('tags')
        revisions_strategy.selectinload('files').joinedload('file')
        return (revisions_strategy,)

    def _check_access(self):
        RHContributionEditableBase._check_access(self)
        if not self.editable.can_see_timeline(session.user):
            raise Forbidden

    def _get_custom_actions(self):
        if not editing_settings.get(self.event, 'service_url'):
            return []

        try:
            return service_get_custom_actions(self.editable, self.editable.latest_revision, session.user)
        except ServiceRequestFailed:
            # unlikely to fail, but if it does we don't break the whole timeline
            return []

    def _process(self):
        custom_actions = self._get_custom_actions()
        custom_actions_ctx = {self.editable.latest_revision: custom_actions}
        schema = EditableSchema(context={
            'user': session.user,
            'custom_actions': custom_actions_ctx,
            'can_see_editor_names': self.editable.can_see_editor_names,
        })
        return schema.jsonify(self.editable)


class RHTriggerExtraRevisionAction(RHContributionEditableRevisionBase):
    """Trigger an extra action provided by the editing service."""

    def _check_revision_access(self):
        if not editing_settings.get(self.event, 'service_url'):
            return False
        # It's up to the editing service to decide who can do what, so we
        # just require the user to have editable access
        return self.editable.can_see_timeline(session.user)

    @use_kwargs({
        'action': fields.String(required=True)
    })
    def _process(self, action):
        ensure_latest_revision(self.revision)
        resp = service_handle_custom_action(self.editable, self.revision, session.user, action)
        return jsonify(redirect=resp.get('redirect'))


class RHCreateEditable(RHContributionEditableBase):
    """Create a new Editable for a contribution."""

    EDITABLE_REQUIRED = False

    def _check_access(self):
        RHContributionEditableBase._check_access(self)
        if not self.contrib.can_submit_proceedings(session.user):
            raise Forbidden
        # TODO: check if submitting papers for editing is allowed in the event
        if self.editable_type.name not in self.contrib.allowed_types_for_editable:
            raise Forbidden

    def _process(self):
        if self.editable:
            raise UserValueError(_('Editable already exists'))

        args = parser.parse({
            'files': EditingFilesField(self.event, self.contrib, self.editable_type, required=True)
        })
        service_url = editing_settings.get(self.event, 'service_url')
        revision_type = RevisionType.new if service_url else RevisionType.ready_for_review

        editable = create_new_editable(self.contrib, self.editable_type, session.user, args['files'], revision_type)
        if service_url:
            try:
                service_handle_new_editable(editable, session.user)
            except ServiceRequestFailed:
                raise ServiceUnavailable(_('Submission failed, please try again later.'))

        return '', 201


class RHDeleteEditable(RHContributionEditableBase):
    """Delete a contribution's editable."""

    def _check_access(self):
        RHContributionEditableBase._check_access(self)
        if not self.editable.can_delete(session.user):
            raise Forbidden

    def _process(self):
        delete_editable(self.editable)
        if editing_settings.get(self.event, 'service_url'):
            try:
                service_handle_delete_editable(self.editable)
            except ServiceRequestFailed:
                raise ServiceUnavailable(_('Deletion failed, please try again later.'))
        return '', 204


class RHReviewEditable(RHContributionEditableRevisionBase):
    """Review the latest revision of an Editable."""

    SERVICE_ALLOWED = True

    def _check_revision_access(self):
        return self.editable.can_perform_editor_actions(session.user)

    @use_kwargs(ReviewEditableArgs)
    def _process_POST(self, action, comment):
        argmap = {'tags': EditingTagsField(self.event, load_default=lambda: set())}
        if action in {EditingReviewAction.update, EditingReviewAction.accept, EditingReviewAction.request_update}:
            argmap['files'] = EditingFilesField(self.event, self.contrib, self.editable_type, allow_claimed_files=True,
                                                required=(action == EditingReviewAction.update))
        args = parser.parse(argmap, unknown=EXCLUDE)
        review_and_publish_editable(self.revision, action, comment, args['tags'], args.get('files'))
        return '', 204

    @use_kwargs({
        'text': fields.String(required=True),
    })
    def _process_PATCH(self, text):
        update_review_comment(self.revision, text)
        return '', 204

    def _process_DELETE(self):
        undo_review(self.revision)
        return '', 204


class RHConfirmEditableChanges(RHContributionEditableRevisionBase):
    """Confirm/reject the changes made by the editor on an Editable."""

    def _check_revision_access(self):
        return self.editable.can_perform_submitter_actions(session.user)

    @use_kwargs({
        'action': EnumField(EditingConfirmationAction, required=True),
        'comment': fields.String(load_default='')
    })
    def _process(self, action, comment):
        confirm_and_publish_changes(self.revision, action, comment)
        return '', 204


class RHReplaceRevision(RHContributionEditableRevisionBase):
    """Replace the latest revision of an Editable."""

    SERVICE_ALLOWED = True

    def _check_revision_access(self):
        # this endpoint is microservice-only
        return False

    @use_kwargs({
        'comment': fields.String(load_default=''),
        'revision_type': EnumField(RevisionType)
    })
    def _process(self, comment, revision_type):
        args = parser.parse({
            'tags': EditingTagsField(self.event, allow_system_tags=self.is_service_call, load_default=lambda: set()),
            'files': EditingFilesField(self.event, self.contrib, self.editable_type, allow_claimed_files=True,
                                       required=True)
        }, unknown=EXCLUDE)

        user = User.get_system_user() if self.is_service_call else session.user
        replace_revision(self.revision, user, comment, args['files'], args['tags'], revision_type)
        return '', 204


class RHCreateSubmitterRevision(RHContributionEditableRevisionBase):
    """Create new revision from submitter."""

    def _check_revision_access(self):
        return self.editable.can_perform_submitter_actions(session.user)

    def _process(self):
        args = parser.parse({
            'files': EditingFilesField(self.event, self.contrib, self.editable_type, allow_claimed_files=True,
                                       required=True)
        })

        service_url = editing_settings.get(self.event, 'service_url')
        new_revision = create_submitter_revision(self.revision, session.user, args['files'])

        if service_url:
            try:
                service_handle_review_editable(self.editable, session.user, EditingReviewAction.update,
                                               self.revision, new_revision)
            except ServiceRequestFailed:
                raise ServiceUnavailable(_('Failed processing review, please try again later.'))
        return '', 204


class RHCreateRevisionComment(RHContributionEditableRevisionBase):
    """Create new revision comment."""

    SERVICE_ALLOWED = True

    def _check_revision_access(self):
        return self.editable.can_comment(session.user)

    @use_kwargs({
        'text': fields.String(required=True, validate=not_empty),
        'internal': fields.Bool(load_default=False)
    })
    def _process(self, text, internal):
        user = session.user
        if self.is_service_call:
            user = User.get_system_user()
        elif internal and not self.editable.can_use_internal_comments(session.user):
            internal = False

        create_revision_comment(self.revision, user, text, internal)
        return '', 201


class RHEditRevisionComment(RHContributionEditableRevisionBase):
    """Edit/delete revision comment."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.comment
        }
    }

    def _process_args(self):
        RHContributionEditableRevisionBase._process_args(self)
        self.comment = (EditingRevisionComment.query
                        .with_parent(self.revision)
                        .filter_by(id=request.view_args['comment_id'])
                        .first_or_404())

    def _check_revision_access(self):
        return self.comment.can_modify(session.user)

    @use_kwargs({
        'text': fields.String(load_default=None, validate=not_empty),
        'internal': fields.Bool(load_default=None)
    })
    def _process_PATCH(self, text, internal):
        updates = {}
        if text is not None:
            updates['text'] = text
        if internal is not None and self.editable.can_use_internal_comments(session.user):
            updates['internal'] = internal
        if updates:
            update_revision_comment(self.comment, updates)
        return '', 204

    def _process_DELETE(self):
        delete_revision_comment(self.comment)
        return '', 204


class RHExportRevisionFiles(RHContributionEditableRevisionBase):
    """Export revision files as a ZIP archive."""

    def _check_revision_access(self):
        return self.editable.can_see_timeline(session.user)

    def _process(self):
        buf = BytesIO()
        with ZipFile(buf, 'w', allowZip64=True) as zip_handler:
            for revision_file in self.revision.files:
                file = revision_file.file
                filename = secure_filename(file.filename, f'file-{file.id}')
                file_type = revision_file.file_type
                folder_name = secure_filename(file_type.name, f'file-type-{file_type.id}')
                first_revision = min(file.editing_revision_files, key=attrgetter('revision.created_dt')).revision
                info = ZipInfo(filename=os.path.join(folder_name, filename),
                               date_time=first_revision.created_dt.astimezone(self.event.tzinfo).timetuple()[:6])
                info.external_attr = 0o644 << 16
                with file.storage.open(file.storage_file_id) as src, zip_handler.open(info, 'w') as dest:
                    shutil.copyfileobj(src, dest, 1024*8)
        zip_filename = f'revision-{self.revision.id}.zip'
        if self.contrib.code:
            zip_filename = f'{self.contrib.code}-{zip_filename}'

        buf.seek(0)
        return send_file(zip_filename, buf, 'application/zip', inline=False)


class RHDownloadRevisionFile(RHContributionEditableRevisionBase):
    """Download a revision file."""

    SERVICE_ALLOWED = True

    normalize_url_spec = {
        'locators': {
            lambda self: self.revision_file
        }
    }

    def _process_args(self):
        RHContributionEditableRevisionBase._process_args(self)
        self.revision_file = (EditingRevisionFile.query
                              .with_parent(self.revision)
                              .filter_by(file_id=request.view_args['file_id'])
                              .first_or_404())

    def _check_revision_access(self):
        if (self.editable.published_revision and self.revision_file in self.editable.published_revision.files
                and self.revision_file.file_type.publishable):
            return self.contrib.can_access(session.user)
        return self.editable.can_see_timeline(session.user)

    def _process(self):
        return self.revision_file.file.send()


class RHEditableUnassign(RHContributionEditableBase):
    def _check_access(self):
        RHContributionEditableBase._check_access(self)
        if not self.editable.can_unassign(session.user):
            raise Forbidden(_('You do not have the permission to unassign this user'))

    def _process_DELETE(self):
        unassign_editor(self.editable)
        return '', 204


class RHEditableAssignMe(RHContributionEditableBase):
    def _check_access(self):
        RHContributionEditableBase._check_access(self)
        if self.editable.editor:
            raise NoReportError.wrap_exc(Conflict(_('This editable already has an editor assigned')))
        if not self.editable.can_assign_self(session.user):
            raise Forbidden(_('You do not have the permission to assign yourself'))

    def _process_PUT(self):
        assign_editor(self.editable, session.user)
        return '', 204
