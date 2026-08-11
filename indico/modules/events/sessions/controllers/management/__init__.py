# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import request, session
from marshmallow import fields
from werkzeug.exceptions import Forbidden

from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.sessions.models.sessions import Session
from indico.web.args import use_kwargs


class RHManageSessionsBase(RHManageEventBase):
    """Base RH for all session management RHs."""


class RHManageSessionBase(RHManageSessionsBase):
    """Base RH for management of a single session."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.session
        }
    }

    def _process_args(self):
        RHManageSessionsBase._process_args(self)
        self.session = Session.get_or_404(request.view_args['session_id'], is_deleted=False)

    def _check_access(self):
        if not self.session.can_manage(session.user):
            raise Forbidden


class RHManageSessionsActionsBase(RHManageSessionsBase):
    """Base class for classes performing actions on sessions."""

    _allow_get_all = False

    @use_kwargs({
        'session_ids': fields.List(fields.Int(), data_key='session_id', load_default=lambda: [])
    })
    def _process_args(self, session_ids):
        RHManageSessionsBase._process_args(self)
        query = Session.query.with_parent(self.event)
        if request.method == 'POST' or not self._allow_get_all:
            # if it's POST we filter by session ids; otherwise we assume
            # the user wants everything (e.g. API-like usage via personal token)
            query = query.filter(Session.id.in_(session_ids))
        self.sessions = query.all()
