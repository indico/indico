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

from flask import session

from MaKaC.accessControl import AccessWrapper
from MaKaC.webinterface.pages.base import WPDecorated, WPJinjaMixin
from indico.core.db import DBMgr


class WPErrorWSGI(WPDecorated, WPJinjaMixin):
    def __init__(self, message, description):
        WPDecorated.__init__(self, None)
        self._message = message
        self._description = description

    def _getBody(self, params):
        return self._getPageContent({
            '_jinja_template': 'error.html',
            'error_message': self._message,
            'error_description': self._description
        })

    def _getAW(self):
        return AccessWrapper(session.avatar)

    def getHTML(self):
        with DBMgr.getInstance().global_connection():
            return self.display()
