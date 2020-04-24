# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import jsonify, request

from indico.core.errors import UserValueError
from indico.modules.events.editing.controllers.base import RHEditableTypeManagementBase, RHEditingManagementBase
from indico.modules.events.editing.models.editable import EditableType
from indico.modules.events.editing.models.file_types import EditingFileType
from indico.modules.events.editing.models.review_conditions import EditingReviewCondition
from indico.modules.events.editing.models.revision_files import EditingRevisionFile
from indico.modules.events.editing.models.tags import EditingTag
from indico.modules.events.editing.operations import (create_new_file_type, create_new_review_condition, create_new_tag,
                                                      delete_file_type, delete_review_condition, delete_tag,
                                                      update_file_type, update_review_condition, update_tag)
from indico.modules.events.editing.schemas import (EditableFileTypeArgs, EditableTagArgs, EditableTypeArgs,
                                                   EditableTypePrincipalsSchema, EditingFileTypeSchema,
                                                   EditingReviewConditionArgs, EditingTagSchema)
from indico.modules.events.editing.settings import editable_type_settings, editing_settings
from indico.util.i18n import _
from indico.web.args import use_kwargs, use_rh_args, use_rh_kwargs


class RHCreateTag(RHEditingManagementBase):
    """Create a new tag."""

    SERVICE_ALLOWED = True

    @use_rh_args(EditableTagArgs)
    def _process(self, data):
        tag = create_new_tag(self.event, **data)
        return EditingTagSchema().jsonify(tag)


class RHEditTag(RHEditingManagementBase):
    """Delete/update a tag."""

    SERVICE_ALLOWED = True

    def _process_args(self):
        RHEditingManagementBase._process_args(self)
        self.tag = (EditingTag.query
                    .with_parent(self.event)
                    .filter_by(id=request.view_args['tag_id'])
                    .first_or_404())

    @use_rh_args(EditableTagArgs, partial=True)
    def _process_PATCH(self, data):
        update_tag(self.tag, **data)
        return EditingTagSchema().jsonify(self.tag)

    def _process_DELETE(self):
        delete_tag(self.tag)
        return '', 204


class RHCreateFileType(RHEditingManagementBase):
    """Create a new file type."""

    SERVICE_ALLOWED = True

    def _process_args(self):
        RHEditingManagementBase._process_args(self)
        self.editable_type = EditableType[request.view_args['type']]

    @use_rh_args(EditableFileTypeArgs)
    def _process(self, data):
        file_type = create_new_file_type(self.event, self.editable_type, **data)
        return EditingFileTypeSchema().jsonify(file_type)


class RHEditFileType(RHEditingManagementBase):
    """Delete/update a file type."""

    SERVICE_ALLOWED = True

    def _process_args(self):
        RHEditingManagementBase._process_args(self)
        self.editable_type = EditableType[request.view_args['type']]
        self.file_type = (EditingFileType.query
                          .with_parent(self.event)
                          .filter_by(id=request.view_args['file_type_id'], type=self.editable_type)
                          .first_or_404())

    @use_rh_args(EditableFileTypeArgs, partial=True)
    def _process_PATCH(self, data):
        update_file_type(self.file_type, **data)
        return EditingFileTypeSchema().jsonify(self.file_type)

    def _process_DELETE(self):
        if EditingRevisionFile.query.with_parent(self.file_type).has_rows():
            raise UserValueError(_('Cannot delete file type which already has files'))

        if self.file_type.review_conditions:
            raise UserValueError(_('Cannot delete file type which is used in a review condition'))
        if self.file_type.publishable:
            is_last = not (EditingFileType.query
                           .with_parent(self.event)
                           .filter(EditingFileType.publishable, EditingFileType.id != self.file_type.id)
                           .has_rows())
            if is_last:
                raise UserValueError(_('Cannot delete the only publishable file type'))
        delete_file_type(self.file_type)
        return '', 204


class RHEditingReviewConditions(RHEditingManagementBase):
    def _process_args(self):
        RHEditingManagementBase._process_args(self)
        self.editable_type = EditableType[request.view_args['type']]

    def _process_GET(self):
        query = (EditingReviewCondition.query.with_parent(self.event)
                 .filter_by(type=self.editable_type)
                 .order_by(EditingReviewCondition.id))
        return jsonify([[cond.id, sorted(ft.id for ft in cond.file_types)] for cond in query])

    @use_rh_kwargs(EditingReviewConditionArgs)
    def _process_POST(self, file_types):
        full_file_types = set(EditingFileType.query.with_parent(self.event).filter(EditingFileType.id.in_(file_types)))
        create_new_review_condition(self.event, self.editable_type, full_file_types)
        return '', 204


class RHEditingEditReviewCondition(RHEditingManagementBase):
    def _process_args(self):
        RHEditingManagementBase._process_args(self)
        self.editable_type = EditableType[request.view_args['type']]
        id_ = request.view_args['condition_id']
        self.condition = EditingReviewCondition.query.with_parent(self.event).filter_by(id=id_).first_or_404()

    def _process_DELETE(self):
        delete_review_condition(self.condition)
        return '', 204

    @use_rh_kwargs(EditingReviewConditionArgs)
    def _process_PATCH(self, file_types):
        full_file_types = set(EditingFileType.query.with_parent(self.event).filter(EditingFileType.id.in_(file_types)))
        update_review_condition(self.condition, full_file_types)
        return '', 204


class RHEnabledEditableTypes(RHEditingManagementBase):
    SERVICE_ALLOWED = True

    def _process_GET(self):
        return jsonify(editing_settings.get(self.event, 'editable_types'))

    @use_kwargs(EditableTypeArgs)
    def _process_POST(self, editable_types):
        editable_types_names = [t.name for t in editable_types]
        editing_settings.set(self.event, 'editable_types', editable_types_names)
        return '', 204


class RHEditableSetSelfAssign(RHEditableTypeManagementBase):
    def _process_GET(self):
        return jsonify(editable_type_settings[self.editable_type].get(self.event, 'self_assign_allowed'))

    def _process_PUT(self):
        editable_type_settings[self.editable_type].set(self.event, 'self_assign_allowed', True)
        return '', 204

    def _process_DELETE(self):
        editable_type_settings[self.editable_type].set(self.event, 'self_assign_allowed', False)


class RHEditableTypePrincipals(RHEditableTypeManagementBase):
    def _process_GET(self):
        permission_name = self.editable_type.editor_permission
        return jsonify([p.principal.identifier for p in self.event.acl_entries
                       if p.has_management_permission(permission_name, explicit=True)])

    @use_rh_kwargs(EditableTypePrincipalsSchema)
    def _process_POST(self, principals):
        permission_name = self.editable_type.editor_permission
        old_principals = {p.principal for p in self.event.acl_entries
                          if p.has_management_permission(permission_name, explicit=True)}
        for p in principals - old_principals:
            self.event.update_principal(p, add_permissions={permission_name})
        for p in old_principals - principals:
            self.event.update_principal(p, del_permissions={permission_name})
        return '', 204
