# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.editing.controllers.base import RHContributionEditableBase
from indico.modules.events.editing.views import WPEditing


class RHEditableTimeline(RHContributionEditableBase):
    def _process(self):
        return WPEditing.render_template(
            'editing.html',
            self.event,
            editable=self.editable,
            contribution=self.contrib
        )
