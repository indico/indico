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

from indico.legacy.webinterface.general import WebFactory
from indico.legacy.webinterface.pages import conferences


class WebFactory(WebFactory):
    id = 'lecture'
    name = "Lecture"
    description = """select this type if you want to set up a simple event thing without schedule, sessions, contributions, ... """


SimpleEventWebFactory = WebFactory


class WPSimpleEventDisplay(conferences.WPConferenceDisplayBase):
    def _getHeader(self):
        return conferences.render_event_header(self._conf.as_event).encode('utf-8')

    def _getBody(self, params):
        raise NotImplementedError
