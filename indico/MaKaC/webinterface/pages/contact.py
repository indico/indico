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
from MaKaC.common.info import HelperMaKaCInfo
from indico.core.config import Config


class WPContact(WPMainBase):
    def _getNavigationDrawer(self):
        return wcomponents.WSimpleNavigationDrawer("Contact", urlHandlers.UHContact.getURL )

    def _getBody(self, params):
        wc = WContact()
        return wc.getHTML()


class WContact(wcomponents.WTemplated):

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["supportEmail"] = Config.getInstance().getPublicSupportEmail()
        vars["teamEmail"] = Config.getInstance().getSupportEmail()
        return vars
