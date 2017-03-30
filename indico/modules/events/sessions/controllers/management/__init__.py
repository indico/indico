# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from flask import request, session
from werkzeug.exceptions import Forbidden

from indico.modules.events.sessions.models.sessions import Session
from indico.legacy.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHManageSessionsBase(RHConferenceModifBase):
    """Base RH for all session management RHs"""

    CSRF_ENABLED = True


class RHManageSessionBase(RHManageSessionsBase):
    """Base RH for management of a single session"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.session
        }
    }

    def _checkParams(self, params):
        RHManageSessionsBase._checkParams(self, params)
        self.session = Session.get_one(request.view_args['session_id'], is_deleted=False)

    def _checkProtection(self):
        if not self.session.can_manage(session.user):
            raise Forbidden


class RHManageSessionsActionsBase(RHManageSessionsBase):
    """Base class for classes performing actions on sessions"""

    def _checkParams(self, params):
        RHManageSessionsBase._checkParams(self, params)
        session_ids = set(map(int, request.form.getlist('session_id')))
        self.sessions = Session.query.with_parent(self.event_new).filter(Session.id.in_(session_ids)).all()
