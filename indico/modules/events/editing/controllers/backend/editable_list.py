# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import uuid

from flask import jsonify, request, session
from marshmallow import fields
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import and_, func, over
from werkzeug.exceptions import Forbidden

from indico.core.db import db
from indico.legacy.common.cache import GenericCache
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.editing.controllers.base import (RHEditablesBase, RHEditableTypeEditorBase,
                                                            RHEditableTypeManagementBase)
from indico.modules.events.editing.models.editable import Editable
from indico.modules.events.editing.models.revision_files import EditingRevisionFile
from indico.modules.events.editing.models.revisions import EditingRevision
from indico.modules.events.editing.operations import assign_editor, generate_editables_zip, unassign_editor
from indico.modules.events.editing.schemas import EditableBasicSchema, EditingEditableListSchema, FilteredEditableSchema
from indico.modules.files.models.files import File
from indico.util.i18n import _
from indico.util.marshmallow import Principal
from indico.web.args import use_kwargs
from indico.web.flask.util import url_for


archive_cache = GenericCache('editables-archive')


class RHEditableList(RHEditableTypeEditorBase):
    """Return the list of editables of the event for a given type."""
    def _process_args(self):
        RHEditableTypeEditorBase._process_args(self)
        self.contributions = (Contribution.query
                              .with_parent(self.event)
                              .options(joinedload('editables'))
                              .order_by(Contribution.friendly_id)
                              .all())

    def _process(self):
        return (EditingEditableListSchema(many=True, context={'editable_type': self.editable_type})
                .jsonify(self.contributions))


class RHPrepareEditablesArchive(RHEditablesBase):
    def _process(self):
        key = unicode(uuid.uuid4())
        data = [editable.id for editable in self.editables]
        archive_cache.set(key, data, time=1800)
        download_url = url_for('.download_archive', self.event, type=self.editable_type.name, uuid=key)
        return jsonify(download_url=download_url)


class RHDownloadArchive(RHEditableTypeManagementBase):
    def _process(self):
        editable_ids = archive_cache.get(unicode(request.view_args['uuid']), [])
        editables = Editable.query.filter(Editable.id.in_(editable_ids)).all()
        return generate_editables_zip(editables)


class RHAssignEditor(RHEditablesBase):
    @use_kwargs({
        'editor': Principal(required=True)
    })
    def _process_args(self, editor):
        RHEditablesBase._process_args(self)
        if (not self.event.can_manage(editor, self.editable_type.editor_permission)
                and not self.event.can_manage(editor, 'editing_manager')):
            raise Forbidden(_('This user is not an editor of the {} type').format(self.editable_type.name))

        self.editor = editor

    def _process(self):
        editables = [e for e in self.editables if e.editor != self.editor]
        for editable in editables:
            assign_editor(editable, self.editor)
        return EditableBasicSchema(many=True).jsonify(editables)


class RHAssignMyselfAsEditor(RHEditablesBase):
    def _check_access(self):
        RHEditablesBase._check_access(self)
        if (not self.event.can_manage(session.user, self.editable_type.editor_permission)
                and not self.event.can_manage(session.user, 'editing_manager')):
            raise Forbidden(_('You are not an editor of the {} type').format(self.editable_type.name))

    def _process(self):
        editables = [e for e in self.editables if e.editor != session.user]
        for editable in editables:
            assign_editor(editable, session.user)
        return EditableBasicSchema(many=True).jsonify(editables)


class RHUnassignEditor(RHEditablesBase):
    def _process(self):
        editables = [e for e in self.editables if e.editor]
        for editable in editables:
            unassign_editor(editable)
        return EditableBasicSchema(many=True).jsonify(editables)


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
        return (Editable.query
                .join(revision_query, revision_query.c.editable_id == Editable.id)
                .options(joinedload('contribution'))
                .all())

    @use_kwargs({
        'has_files': fields.Dict(keys=fields.Int, values=fields.Bool, missing={}),
        'extensions': fields.Dict(keys=fields.Int, values=fields.List(fields.String()), missing={}),
    })
    def _process(self, has_files, extensions):
        editables = self._query_editables(has_files, extensions)
        return FilteredEditableSchema(many=True, context={'user': session.user}).jsonify(editables)
