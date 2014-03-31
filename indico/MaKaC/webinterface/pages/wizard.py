# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

import MaKaC.webinterface.pages.main as base, main
import MaKaC.webinterface.wcomponents as wcomponents
from MaKaC.i18n import _
from MaKaC.webinterface.common.timezones import TimezoneRegistry

from tzlocal import get_localzone
from xml.sax.saxutils import quoteattr

from indico.web.flask.util import url_for


class WWizard(wcomponents.WTemplated):

    def __init__(self, params):
        self._params = params

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["name"] = quoteattr(self._params.get("name", ""))
        wvars["surName"] = quoteattr(self._params.get("surName", ""))
        wvars["userEmail"] = quoteattr(self._params.get("userEmail", ""))
        wvars["login"] = quoteattr(self._params.get("login", ""))
        wvars["organisation"] = quoteattr(self._params.get("organisation", ""))
        tz = str(get_localzone())
        wvars["timezoneOptions"] = TimezoneRegistry.getShortSelectItemsHTML(tz)
        wvars["instanceTrackingEmail"] = quoteattr(self._params.get("instanceTrackingEmail", ""))
        wvars["msg"] = self._params.get("msg", "")
        wvars["checked"] = self._params.get("accept", "")
        return wvars


class WPWizard(main.WPMainBase):

    def __init__(self, rh, params):
        self._params = params
        main.WPMainBase.__init__(self, rh)

    def _getTitle(self):
        return "{} - {}".format(main.WPMainBase._getTitle(self), _("Admin Creation Wizard"))

    def _getBody(self, params):
        wc = WWizard(self._params)
        return wc.getHTML()


class WPAdminCreated(base.WPDecorated):

    def __init__(self, rh, av):
        base.WPDecorated.__init__(self, rh)
        self._av = av

    def _getBody(self, params):
        wc = wcomponents.WAdminCreated(self._av)
        params["loginURL"] = url_for('auth.login')

        return wc.getHTML(params)
