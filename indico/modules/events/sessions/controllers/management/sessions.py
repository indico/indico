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

from indico.modules.events.sessions.controllers.management import RHManageSessionsBase
from indico.modules.events.sessions.util import get_colors, get_active_sessions
from indico.modules.events.sessions.views import WPManageSessions


class RHSessionsList(RHManageSessionsBase):
    """Display list of all sessions within the event"""

    def _process(self):
        return WPManageSessions.render_template('management/session_list.html', self.event_new.as_legacy,
                                                event=self.event_new, sessions=get_active_sessions(self.event_new),
                                                default_colors=get_colors())
