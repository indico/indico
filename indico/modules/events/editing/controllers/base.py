# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import request

from indico.modules.events.contributions.controllers.display import RHContributionDisplayBase
from indico.modules.events.controllers.base import RHDisplayEventBase
from indico.modules.events.editing.models.editable import Editable, EditableType
from indico.modules.events.management.controllers.base import RHManageEventBase
from indico.web.rh import RequireUserMixin


class RHEditingBase(RequireUserMixin, RHDisplayEventBase):
    """Base class for editing RHs that don't reference an editable."""

    EVENT_FEATURE = 'editing'

    def _check_access(self):
        RHDisplayEventBase._check_access(self)
        RequireUserMixin._check_access(self)


class RHEditingManagementBase(RHManageEventBase):
    """Base class for editing RHs that don't reference an editable."""

    EVENT_FEATURE = 'editing'
    PERMISSION = 'editing_manager'


class RHEditableTypeManagementBase(RHEditingManagementBase):
    """Base class for editable type RHs."""

    def _process_args(self):
        RHManageEventBase._process_args(self)
        self.editable_type = EditableType[request.view_args['type']]


class RHContributionEditableBase(RequireUserMixin, RHContributionDisplayBase):
    """Base class for operations on an editable."""

    EVENT_FEATURE = 'editing'

    normalize_url_spec = {
        'locators': {
            lambda self: self.contrib
        },
        'preserved_args': {'type'}
    }

    def _check_access(self):
        RequireUserMixin._check_access(self)
        RHContributionDisplayBase._check_access(self)

    def _process_args(self):
        RHContributionDisplayBase._process_args(self)
        self.editable_type = EditableType[request.view_args['type']]
        self.editable = (Editable.query
                         .with_parent(self.contrib)
                         .filter_by(type=self.editable_type)
                         .first())
