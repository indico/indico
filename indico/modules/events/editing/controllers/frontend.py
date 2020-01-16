# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from werkzeug.exceptions import NotFound

from indico.modules.events.editing.controllers.base import (RHContributionEditableBase, RHEditingBase,
                                                            RHEditingManagementBase)
from indico.modules.events.editing.views import WPEditing


class RHEditingDashboard(RHEditingBase):
    def _process(self):
        return WPEditing.render_template('management/editing.html', self.event)


class RHEditableTimeline(RHContributionEditableBase):
    def _process_args(self):
        RHContributionEditableBase._process_args(self)
        if not self.editable:
            raise NotFound

    def _process(self):
        return WPEditing.render_template(
            'timeline.html',
            self.event,
            editable=self.editable,
            contribution=self.contrib
        )


class RHManageEditingTags(RHEditingManagementBase):
    def _process(self):
        return WPEditing.render_template('management/tags.html', self.event)


class RHManageEditingFileTypes(RHEditingManagementBase):
    def _process(self):
        return WPEditing.render_template('management/filetypes.html', self.event)
