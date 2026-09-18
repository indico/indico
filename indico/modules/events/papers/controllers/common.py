# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.papers.controllers.base import RHPapersBase
from indico.modules.events.papers.file_types import PaperFileType
from indico.modules.events.papers.schemas import PaperFileTypeSchema
from indico.modules.events.papers.settings import paper_submission_settings


class RHPapersFileTypes(RHPapersBase):
    """Return all file types defined in the event for paper reviewing."""

    def _process(self):
        query = PaperFileType.query.with_parent(self.event)
        if not paper_submission_settings.get(self.event, 'auto_submission_to_editing'):
            query = query.filter_by(source_editing_file_type_id=None)
        file_types = query.all()
        return PaperFileTypeSchema(many=True).jsonify(file_types)
