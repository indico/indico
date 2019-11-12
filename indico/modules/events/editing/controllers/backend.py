# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from marshmallow import fields

from indico.modules.events.controllers.base import RHEventBase
from indico.modules.events.editing.models.editable import Editable
from indico.modules.events.editing.schemas import EditableSchema, EditingFileTypeSchema, EditingTagSchema
from indico.web.args import use_kwargs


class RHEditingFileTypes(RHEventBase):
    def _process(self):
        return EditingFileTypeSchema(many=True).jsonify(self.event.editing_file_types)


class RHEditingTags(RHEventBase):
    def _process(self):
        return EditingTagSchema(many=True).jsonify(self.event.editing_tags)


class RHEditable(RHEventBase):
    @use_kwargs({
        'editable_id': fields.Int(location='view_args'),
    })
    def _process_args(self, editable_id):
        RHEventBase._process_args(self)
        self.editable = Editable.query.get(editable_id)
        # TODO: check that the editable belongs to the correct event/contribution/type!

    def _process(self):
        return EditableSchema().jsonify(self.editable)
