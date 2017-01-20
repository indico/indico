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

from flask import render_template, session

from MaKaC.accessControl import AccessWrapper
from MaKaC.common import Config
from MaKaC.webinterface.pages.base import WPDecorated, WPJinjaMixin


def render_error(message, description, standalone=False):
    if standalone:
        logo_url = Config.getInstance().getSystemIconURL("logoIndico")
        return render_template('standalone_error.html', error_message=message, error_description=description,
                               logo_url=logo_url)
    else:
        return WPErrorWSGI(message, description).getHTML()


class WPErrorWSGI(WPDecorated, WPJinjaMixin):
    SOCIAL_ENABLED = False

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
        return self.display()
