# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.editing.controllers.base import RHEditingBase
from indico.modules.events.editing.schemas import EditingFileTypeSchema, EditingTagSchema


class RHEditingFileTypes(RHEditingBase):
    """Return all editing file types defined in the event."""

    def _process(self):
        return EditingFileTypeSchema(many=True).jsonify(self.event.editing_file_types)


class RHEditingTags(RHEditingBase):
    """Return all editing tags defined in the event."""

    def _process(self):
        return EditingTagSchema(many=True).jsonify(self.event.editing_tags)
