# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import request

from indico.modules.events.editing.controllers.base import RHEditingManagementBase
from indico.modules.events.editing.models.file_types import EditingFileType
from indico.modules.events.editing.models.tags import EditingTag
from indico.modules.events.editing.operations import (create_new_file_type, create_new_tag, delete_file_type,
                                                      delete_tag, update_file_type, update_tag)
from indico.modules.events.editing.schemas import (EditableFileTypeArgs, EditableTagArgs, EditingFileTypeSchema,
                                                   EditingTagSchema)
from indico.web.args import use_rh_args


class RHCreateTag(RHEditingManagementBase):
    """Create a new tag."""

    @use_rh_args(EditableTagArgs)
    def _process(self, data):
        tag = create_new_tag(self.event, **data)
        return EditingTagSchema().jsonify(tag)


class RHEditTag(RHEditingManagementBase):
    """Delete/update a tag."""

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

    @use_rh_args(EditableFileTypeArgs)
    def _process(self, data):
        file_type = create_new_file_type(self.event, **data)
        return EditingFileTypeSchema().jsonify(file_type)


class RHEditFileType(RHEditingManagementBase):
    """Delete/update a file type."""

    def _process_args(self):
        RHEditingManagementBase._process_args(self)
        self.file_type = (EditingFileType.query
                          .with_parent(self.event)
                          .filter_by(id=request.view_args['file_type_id'])
                          .first_or_404())

    @use_rh_args(EditableFileTypeArgs, partial=True)
    def _process_PATCH(self, data):
        update_file_type(self.file_type, **data)
        return EditingFileTypeSchema().jsonify(self.file_type)

    def _process_DELETE(self):
        delete_file_type(self.file_type)
        return '', 204
