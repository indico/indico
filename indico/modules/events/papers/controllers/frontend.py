# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.papers.controllers.base import RHManagePapersBase
from indico.modules.events.papers.views import WPManagePapers


class RHPapersDashboard(RHManagePapersBase):
    EVENT_FEATURE = None

    def _process(self):
        template = 'file_types.html' if self.event.has_feature('papers') else 'disabled.html'
        return WPManagePapers.render_template(f'management/{template}', self.event)
