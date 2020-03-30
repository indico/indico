# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import request, session
from werkzeug.exceptions import Forbidden, NotFound

from indico.modules.events.editing.controllers.base import (RHContributionEditableBase, RHEditableTypeManagementBase,
                                                            RHEditingManagementBase)
from indico.modules.events.editing.models.editable import EditableType
from indico.modules.events.editing.views import WPEditing


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

        if self.event.can_manage(session.user, permission='paper_editing'):
            return
        if not self._user_is_authorized_submitter() and not self._user_is_authorized_editor():
            raise Forbidden

    def _process(self):
        return WPEditing.render_template(
            'editing.html',
            self.event,
            editable=self.editable,
            contribution=self.contrib
        )


class RHManageEditingTags(RHEditingManagementBase):
    def _process(self):
        return WPEditing.render_template('management/tags.html', self.event)


class RHManageEditingFileTypes(RHEditingManagementBase):
    def _process_args(self):
        RHEditingManagementBase._process_args(self)
        self.editable_type = EditableType[request.view_args['type']]

    def _process(self):
        return WPEditing.render_template('management/filetypes.html', self.event,
                                         editable_type=self.editable_type)


class RHManageEditingReviewConditions(RHEditingManagementBase):
    def _process_args(self):
        RHEditingManagementBase._process_args(self)
        self.editable_type = EditableType[request.view_args['type']]

    def _process(self):
        return WPEditing.render_template('management/review_conditions.html', self.event,
                                         editable_type=self.editable_type)


class RHManageEditableType(RHEditableTypeManagementBase):
    def _process(self):
        return WPEditing.render_template('management/editable_type.html', self.event, type=self.editable_type)
