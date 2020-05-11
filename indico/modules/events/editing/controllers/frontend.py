# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import session
from werkzeug.exceptions import Forbidden, NotFound

from indico.modules.events.editing.controllers.base import RHContributionEditableBase, RHEditingManagementBase
from indico.modules.events.editing.views import WPEditing, WPEditingView


class RHEditingDashboard(RHEditingManagementBase):
    EVENT_FEATURE = None

    def _process(self):
        template = 'editing.html' if self.event.has_feature('editing') else 'disabled.html'
        return WPEditing.render_template('management/{}'.format(template), self.event)


class RHEditableTimeline(RHContributionEditableBase):
    def _process_args(self):
        RHContributionEditableBase._process_args(self)
        if not self.editable:
            raise NotFound

    def _check_access(self):
        RHContributionEditableBase._check_access(self)
        if not self.editable.can_see_timeline(session.user):
            raise Forbidden

    def _process(self):
        return WPEditingView.render_template(
            'editing.html',
            self.event,
            editable=self.editable,
            contribution=self.contrib
        )
