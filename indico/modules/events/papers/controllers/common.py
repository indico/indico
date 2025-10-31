# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.papers.controllers.base import RHPapersBase
from indico.modules.events.papers.file_types import PaperFileType
from indico.modules.events.papers.schemas import PaperFileTypeSchema


class RHPapersFileTypes(RHPapersBase):
    """Return all editing file types defined in the event for the editable type."""

    def _process_args(self):
        RHPapersBase._process_args(self)
        self.editing_file_types = PaperFileType.query.with_parent(self.event).all()

    def _process(self):
        return PaperFileTypeSchema(many=True).jsonify(self.editing_file_types)
