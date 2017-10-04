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

from flask import session

from indico.legacy.webinterface.pages.base import WPDecorated
from indico.legacy.webinterface.wcomponents import WTemplated
from indico.util.i18n import _
from indico.web.flask.util import url_for


class WPKeyAccessError(WPDecorated):
    def __init__(self, rh):
        WPDecorated.__init__(self, rh)

    def _getBody(self, params):
        event = self._rh.event
        msg = ''
        if session.get('access_keys', {}).get(event._access_key_session_key) is not None:
            msg = '<span style="color: red;">{}</span>'.format(_("Bad access key!"))
        return WAccessKeyError(self._rh, msg).getHTML()


class WAccessKeyError(WTemplated):
    def __init__(self, rh, msg=""):
        self._rh = rh
        self._msg = msg

    def getVars(self):
        vars = WTemplated.getVars(self)
        vars["url"] = url_for('event.conferenceDisplay-accessKey', self._rh._target)
        vars["msg"] = self._msg
        return vars
