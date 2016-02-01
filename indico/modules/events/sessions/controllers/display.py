# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from flask import session
from werkzeug.exceptions import Forbidden

from indico.modules.events.sessions.util import get_sessions_for_user
from indico.modules.events.sessions.views import WPDisplayMySessionsConference
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


class RHDisplaySessionList(RHConferenceBaseDisplay):
    def _checkProtection(self):
        if not session.user:
            raise Forbidden
        RHConferenceBaseDisplay._checkProtection(self)

    def _process(self):
        sessions = get_sessions_for_user(self.event_new, session.user)
        return WPDisplayMySessionsConference.render_template('display/session_list.html', self._conf,
                                                             event=self.event_new, sessions=sessions)
