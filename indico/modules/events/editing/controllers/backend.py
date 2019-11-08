# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.controllers.base import RHEventBase
from indico.modules.events.editing.schemas import EditingFileTypeSchema


class RHEditingFileTypes(RHEventBase):
    def _process(self):
        return EditingFileTypeSchema(many=True).jsonify(self.event.editing_file_types)
