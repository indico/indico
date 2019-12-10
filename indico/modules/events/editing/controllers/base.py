# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import request, session
from werkzeug.exceptions import Forbidden

from indico.modules.events.contributions.controllers.display import RHContributionDisplayBase
from indico.modules.events.controllers.base import RHEventBase
from indico.modules.events.editing.models.editable import Editable, EditableType
from indico.modules.events.management.controllers.base import RHManageEventBase


class RHEditingBase(RHEventBase):
    """Base class for editing RHs that don't reference an editable."""

    EVENT_FEATURE = 'editing'

    def _check_access(self):
        RHEventBase._check_access(self)
        if not session.user:
            raise Forbidden


class RHEditingManagementBase(RHManageEventBase):
    EVENT_FEATURE = 'editing'


class RHContributionEditableBase(RHContributionDisplayBase):
    """Base class for operations on an editable."""

    EVENT_FEATURE = 'editing'

    normalize_url_spec = {
        'locators': {
            lambda self: self.contrib
        },
        'preserved_args': {'type'}
    }

    def _process_args(self):
        RHContributionDisplayBase._process_args(self)
        self.editable_type = EditableType[request.view_args['type']]
        self.editable = (Editable.query
                         .with_parent(self.contrib)
                         .filter_by(type=self.editable_type)
                         .first())

    def _user_is_authorized_submitter(self):
        if session.user.is_admin:
            # XXX: not sure if we want to keep this, but for now it's useful to have!
            return True
        return self.contrib.is_user_associated(session.user, check_abstract=True)

    def _user_is_authorized_editor(self):
        if session.user.is_admin:
            # XXX: not sure if we want to keep this, but for now it's useful to have!
            return True
        return self.editable.editor == session.user
