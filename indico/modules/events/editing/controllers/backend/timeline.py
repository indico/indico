# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import os
from io import BytesIO
from zipfile import ZipFile

from flask import request, session
from marshmallow import fields
from marshmallow_enum import EnumField
from sqlalchemy.orm import joinedload
from werkzeug.exceptions import Forbidden, NotFound, ServiceUnavailable

from indico.core.db import db
from indico.core.errors import UserValueError
from indico.modules.events.editing.controllers.base import RHContributionEditableBase, TokenAccessMixin
from indico.modules.events.editing.fields import EditingFilesField, EditingTagsField
from indico.modules.events.editing.models.comments import EditingRevisionComment
from indico.modules.events.editing.models.revision_files import EditingRevisionFile
from indico.modules.events.editing.models.revisions import EditingRevision, InitialRevisionState
from indico.modules.events.editing.operations import (assign_editor, confirm_editable_changes, create_new_editable,
                                                      create_revision_comment, create_submitter_revision,
                                                      delete_editable, delete_revision_comment, replace_revision,
                                                      review_editable_revision, unassign_editor, undo_review,
                                                      update_revision_comment)
from indico.modules.events.editing.schemas import (EditableSchema, EditingConfirmationAction, EditingReviewAction,
                                                   ReviewEditableArgs)
from indico.modules.events.editing.service import ServiceRequestFailed, service_handle_new_editable
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


class RHEditingUploadPaperLastRevision(RHEditingUploadFile):
    @use_kwargs({
        'id': fields.Int()
    })
    def _process(self, id):
        last_rev = self.contrib.paper.get_last_revision()
        if last_rev:
            found = next((f for f in last_rev.files if f.id == id), None)
            if found:
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

    def _process(self):
        return EditableSchema(context={'user': session.user}).jsonify(self.editable)


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
        initial_state = InitialRevisionState.new if service_url else InitialRevisionState.ready_for_review

        editable = create_new_editable(self.contrib, self.editable_type, session.user, args['files'], initial_state)
        db.session.commit()
        if service_url:
            try:
                service_handle_new_editable(editable)
            except ServiceRequestFailed:
                delete_editable(editable)
                db.session.commit()
                raise ServiceUnavailable(_('Submission failed, please try again later.'))
        return '', 201


class RHReviewEditable(RHContributionEditableRevisionBase):
    """Review the latest revision of an Editable."""

    def _check_revision_access(self):
        return self.editable.can_perform_editor_actions(session.user)

    @use_kwargs(ReviewEditableArgs)
    def _process(self, action, comment):
        argmap = {'tags': EditingTagsField(self.event, missing=set())}
        if action in (EditingReviewAction.update, EditingReviewAction.update_accept):
            argmap['files'] = EditingFilesField(self.event, self.contrib, self.editable_type, allow_claimed_files=True,
                                                required=True)
        args = parser.parse(argmap)
        review_editable_revision(self.revision, session.user, action, comment, args['tags'], args.get('files'))
        return '', 204


class RHConfirmEditableChanges(RHContributionEditableRevisionBase):
    """Confirm/reject the changes made by the editor on an Editable."""

    def _check_revision_access(self):
        return self.editable.can_perform_submitter_actions(session.user)

    @use_kwargs({
        'action': EnumField(EditingConfirmationAction, required=True),
        'comment': fields.String(missing='')
    })
    def _process(self, action, comment):
        confirm_editable_changes(self.revision, session.user, action, comment)
        return '', 204


class RHReplaceRevision(RHContributionEditableRevisionBase):
    """Replace the latest revision of an Editable."""

    SERVICE_ALLOWED = True

    def _check_revision_access(self):
        # XXX: we still need UI for this or expose it only to the microservice
        return self.editable.editor is None and self.editable.can_perform_submitter_actions(session.user)

    @use_kwargs({
        'comment': fields.String(missing=''),
        'state': EnumField(InitialRevisionState)
    })
    def _process(self, comment, state):
        args = parser.parse({
            'tags': EditingTagsField(self.event, allow_system_tags=self.is_service_call, missing=set()),
            'files': EditingFilesField(self.event, self.contrib, self.editable_type, allow_claimed_files=True,
                                       required=True)
        })

        user = User.get_system_user() if self.is_service_call else session.user
        replace_revision(self.revision, user, comment, args['files'], args['tags'], state)
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

        create_submitter_revision(self.revision, session.user, args['files'])
        return '', 204


class RHUndoReview(RHContributionEditableRevisionBase):
    """Undo the last review/confirmation on an Editable."""

    def _check_revision_access(self):
        return self.editable.can_perform_editor_actions(session.user)

    def _process(self):
        undo_review(self.revision)
        return '', 204


class RHCreateRevisionComment(RHContributionEditableRevisionBase):
    """Create new revision comment"""

    def _check_revision_access(self):
        return self.editable.can_comment(session.user)

    @use_kwargs({
        'text': fields.String(required=True, validate=not_empty),
        'internal': fields.Bool(missing=False)
    })
    def _process(self, text, internal):
        if internal and not self.editable.can_use_internal_comments(session.user):
            internal = False
        create_revision_comment(self.revision, session.user, text, internal)
        return '', 201


class RHEditRevisionComment(RHContributionEditableRevisionBase):
    """Edit/delete revision comment"""

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
        'text': fields.String(missing=None, validate=not_empty),
        'internal': fields.Bool(missing=None)
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
    """Export revision files as a ZIP archive"""

    def _check_revision_access(self):
        return self.editable.can_see_timeline(session.user)

    def _process(self):
        buf = BytesIO()
        with ZipFile(buf, 'w', allowZip64=True) as zip_handler:
            for revision_file in self.revision.files:
                file = revision_file.file
                filename = secure_filename(file.filename, 'file-{}'.format(file.id))
                file_type = revision_file.file_type
                folder_name = secure_filename(file_type.name, 'file-type-{}'.format(file_type.id))

                with file.storage.get_local_path(file.storage_file_id) as filepath:
                    zip_handler.write(filepath, os.path.join(folder_name, filename))

        buf.seek(0)
        return send_file('revision-{}.zip'.format(self.revision.id), buf, 'application/zip', inline=False)


class RHDownloadRevisionFile(RHContributionEditableRevisionBase):
    """Download a revision file"""

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
        if not self.editable.can_assign_self(session.user):
            raise Forbidden(_('You do not have the permission to assign yourself'))

    def _process_PUT(self):
        assign_editor(self.editable, session.user)
        return '', 204
