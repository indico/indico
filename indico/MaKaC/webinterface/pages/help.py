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

import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.webinterface.pages.main import WPMainBase
import MaKaC.webinterface.wcomponents as wcomponents
from MaKaC.webinterface.rh.admins import RCAdmin
from MaKaC.plugins import PluginsHolder
from MaKaC.i18n import _


class WPHelp(WPMainBase):
    def _getNavigationDrawer(self):
        return wcomponents.WSimpleNavigationDrawer(_("Help"), urlHandlers.UHConferenceHelp.getURL)

    def _getBody(self, params):
        wc = WHelp(self._rh)
        return wc.getHTML()


class WHelp(wcomponents.WTemplated):

    def __init__(self, rh):
        self._rh = rh

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["pluginDocs"] = "".join(self._notify("providePluginDocumentation"))
        vars["IsAdmin"] = RCAdmin.hasRights(self._rh)
        return vars
