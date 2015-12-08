# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from flask import request

from indico.modules.events.sessions.models.sessions import Session
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase
from MaKaC.webinterface.rh.base import RH


class RHManageSessionsBase(RHConferenceModifBase):
    """Base RH for all session management RHs"""

    CSRF_ENABLED = True

    def _process(self):
        return RH._process(self)


class RHManageSessionBase(RHManageSessionsBase):
    """Base RH for management of a single session"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.session
        }
    }

    def _checkParams(self, params):
        RHManageSessionsBase._checkParams(self, params)
        self.session = (self.event_new.sessions
                        .filter_by(id=request.view_args['session_id'], is_deleted=False)
                        .first_or_404())


class RHManageSessionsActionsBase(RHManageSessionsBase):
    """Base class for classes performing actions on sessions"""

    def _checkParams(self, params):
        RHManageSessionsBase._checkParams(self, params)
        session_ids = set(map(int, request.form.getlist('session_id')))
        self.sessions = self.event_new.sessions.filter(Session.id.in_(session_ids), ~Session.is_deleted).all()
