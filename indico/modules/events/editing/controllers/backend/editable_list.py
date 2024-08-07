# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import uuid

from flask import jsonify, request, session
from marshmallow import fields, validate
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.sql import and_, func, over
from werkzeug.exceptions import Forbidden

from indico.core.cache import make_scoped_cache
from indico.core.db import db
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.editing.controllers.backend.util import (confirm_and_publish_changes,
                                                                    review_and_publish_editable)
from indico.modules.events.editing.controllers.base import (RHEditablesBase, RHEditableTypeEditorBase,
                                                            RHEditableTypeManagementBase)
from indico.modules.events.editing.models.editable import Editable, EditableState
from indico.modules.events.editing.models.revision_files import EditingRevisionFile
from indico.modules.events.editing.models.revisions import EditingRevision, RevisionType
from indico.modules.events.editing.operations import (assign_editor, create_revision_comment, generate_editables_json,
                                                      generate_editables_zip, unassign_editor)
from indico.modules.events.editing.schemas import (EditableBasicSchema, EditingConfirmationAction,
                                                   EditingEditableListSchema, EditingReviewAction,
                                                   FilteredEditableSchema)
from indico.modules.files.models.files import File
from indico.util.i18n import _
from indico.util.marshmallow import Principal, not_empty
from indico.web.args import use_kwargs
from indico.web.flask.util import url_for


archive_cache = make_scoped_cache('editables-archive')


class RHEditableList(RHEditableTypeEditorBase):
    """Return the list of editables of the event for a given type."""

    def _process_args(self):
        RHEditableTypeEditorBase._process_args(self)
        self.contributions = (Contribution.query
                              .with_parent(self.event)
                              .options(joinedload('editables').selectinload('revisions').selectinload('tags'),
                                       joinedload('person_links'),
                                       joinedload('session'))
                              .order_by(Contribution.friendly_id)
                              .all())

    def _process(self):
        return (EditingEditableListSchema(many=True, context={'editable_type': self.editable_type})
                .jsonify(self.contributions))


class RHPrepareEditablesArchive(RHEditablesBase):
    def _process(self):
        key = str(uuid.uuid4())
        data = [editable.id for editable in self.editables]
        archive_cache.set(key, data, timeout=1800)
        archive_type = request.view_args['archive_type']
        download_url = url_for('.download_archive', self.event, type=self.editable_type.name,
                               archive_type=archive_type, uuid=key)
        return jsonify(download_url=download_url)


class RHDownloadArchive(RHEditableTypeManagementBase):
    def _process(self):
        editable_ids = archive_cache.get(str(request.view_args['uuid']), [])
        revisions_strategy = selectinload('revisions')
        revisions_strategy.subqueryload('comments').joinedload('user')
        revisions_strategy.subqueryload('files').joinedload('file_type')
        revisions_strategy.subqueryload('tags')
        revisions_strategy.joinedload('user')
        editables = (Editable.query
                     .filter(Editable.id.in_(editable_ids), ~Editable.is_deleted)
                     .options(joinedload('editor'), joinedload('contribution'), revisions_strategy)
                     .all())
        fn = {
            'archive': generate_editables_zip,
            'json': generate_editables_json,
        }[request.view_args['archive_type']]
        return fn(self.event, self.editable_type, editables)


class RHEditorAssignmentBase(RHEditablesBase):
    editor = None

    def _check_access(self):
        RHEditablesBase._check_access(self)
        if (self.editor and not self.event.can_manage(self.editor, self.editable_type.editor_permission)
                and not self.event.can_manage(self.editor, 'editing_manager')):
            if self.editor == session.user:
                raise Forbidden(_('You are not an editor of the {} type').format(self.editable_type.name))
            raise Forbidden(_('This user is not an editor of the {} type').format(self.editable_type.name))

    @use_kwargs({
        'editor_assignments': fields.Dict(keys=fields.Int, values=Principal, required=True),
        'force': fields.Bool(load_default=False)
    })
    def _process(self, editor_assignments, force):
        editables = [e for e in self.editables if self._can_assign_editor(e)]
        if not force and not all(e.editor == editor_assignments.get(e.id) for e in editables):
            return jsonify(editor_conflict=True), 409
        for editable in editables:
            self._assign_editor(editable)
        return EditableBasicSchema(many=True).jsonify(editables)

    def _can_assign_editor(self, editable):
        return editable.editor != self.editor

    def _assign_editor(self, editable):
        assign_editor(editable, self.editor)


class RHAssignEditor(RHEditorAssignmentBase):
    @use_kwargs({
        'editor': Principal(required=True)
    })
    def _process_args(self, editor):
        RHEditorAssignmentBase._process_args(self)
        self.editor = editor


class RHAssignMyselfAsEditor(RHEditorAssignmentBase):
    def _process_args(self):
        RHEditorAssignmentBase._process_args(self)
        self.editor = session.user


class RHUnassignEditor(RHEditorAssignmentBase):
    def _can_assign_editor(self, editable):
        return bool(editable.editor)

    def _assign_editor(self, editable):
        unassign_editor(editable)


class RHCreateComment(RHEditablesBase):
    @use_kwargs({
        'text': fields.String(required=True, validate=not_empty),
        'internal': fields.Bool(load_default=False)
    })
    def _process(self, text, internal):
        for editable in self.editables:
            create_revision_comment(editable.latest_revision, session.user, text, internal)
        return '', 201


class RHApplyJudgment(RHEditablesBase):
    @use_kwargs({
        'action': fields.String(required=True, validate=validate.OneOf(['accept', 'reject']))
    })
    def _process(self, action):
        changed = []
        for editable in self.editables:
            revision = editable.latest_revision
            if action == 'accept' and not revision.has_publishable_files:
                continue
            if revision.type == RevisionType.ready_for_review:
                review_and_publish_editable(revision, EditingReviewAction[action], '')
            elif revision.type == RevisionType.needs_submitter_confirmation and action == 'accept':
                confirm_and_publish_changes(revision, EditingConfirmationAction.accept, '')
                db.session.flush()
            else:
                continue
            db.session.expire(editable)
            changed.append(editable)
        return EditableBasicSchema(many=True).jsonify(changed)


class RHFilterEditablesByFileTypes(RHEditableTypeEditorBase):
    """Return the list of editables that have certain files."""

    def _make_revision_file_type_filter(self, subquery, file_type_id, *criteria):
        return EditingRevision.files.any(
            and_(
                EditingRevisionFile.revision_id == subquery.c.id,
                EditingRevisionFile.file_type_id == file_type_id,
                *criteria
            )
        )

    def _query_editables(self, has_files, extensions):
        inner = (
            db.session.query(EditingRevision.id, EditingRevision.editable_id)
            # only get revisions belonging to the correct event + editable type
            .filter(
                EditingRevision.editable.has(
                    and_(
                        Editable.contribution.has(
                            and_(
                                ~Contribution.is_deleted,
                                Contribution.event_id == self.event.id,
                            )
                        ),
                        Editable.type == self.editable_type,
                        Editable.state == EditableState.ready_for_review,
                        ~Editable.is_deleted,
                    )
                )
            )
            # allow filtering by "is latest revision" later
            .add_columns(
                over(
                    func.row_number(),
                    partition_by=EditingRevision.editable_id,
                    order_by=EditingRevision.created_dt.desc(),
                ).label('rownum')
            )
        ).subquery()

        revision_query = (
            db.session.query(EditingRevision.editable_id)
            .select_entity_from(inner)
            .filter(inner.c.rownum == 1)  # only latest revision
        )

        # filter by presence (or lack of) file types
        for file_type_id, present in has_files.items():
            crit = self._make_revision_file_type_filter(inner, file_type_id)
            if not present:
                crit = ~crit
            revision_query = revision_query.filter(crit)

        # filter by having files with certain extensions
        for file_type_id, exts in extensions.items():
            ext_filter = EditingRevisionFile.file.has(File.extension.in_(exts))
            revision_query = revision_query.filter(
                self._make_revision_file_type_filter(inner, file_type_id, ext_filter)
            )

        revision_query = revision_query.subquery()
        contribution_strategy = joinedload('contribution')
        contribution_strategy.selectinload('person_links')
        contribution_strategy.joinedload('session')
        return (Editable.query
                .join(revision_query, revision_query.c.editable_id == Editable.id)
                .options(contribution_strategy)
                .all())

    @use_kwargs({
        'has_files': fields.Dict(keys=fields.Int, values=fields.Bool, load_default=lambda: {}),
        'extensions': fields.Dict(keys=fields.Int, values=fields.List(fields.String()), load_default=lambda: {}),
    })
    def _process(self, has_files, extensions):
        editables = self._query_editables(has_files, extensions)
        return FilteredEditableSchema(many=True, context={'user': session.user}).jsonify(editables)
