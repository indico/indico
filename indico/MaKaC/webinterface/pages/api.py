# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
from operator import attrgetter

from MaKaC.webinterface.pages.admins import WPPersonalArea, WPServicesCommon
from MaKaC.webinterface.wcomponents import WTemplated
from indico.web.http_api.auth import APIKeyHolder

class WPUserAPI(WPPersonalArea):

    def _getTabContent(self, params):
        c = WUserAPI(self._avatar)
        return c.getHTML(params)

    def _setActiveTab(self):
        self._tabAPI.setActive()

class WUserAPI(WTemplated):

    def __init__(self, av):
        self._avatar = av

    def getVars(self):
        vars = WTemplated.getVars(self)
        vars['avatar'] = self._avatar
        vars['apiKey'] = self._avatar.getAPIKey()
        vars['isAdmin'] = self._rh._getUser().isAdmin()
        return vars


class WPAdminAPI(WPServicesCommon):

    def _getTabContent(self, params):
        c = WAdminAPI()
        return c.getHTML(params)

    def _setActiveTab( self ):
        self._subTabHTTPAPI.setActive()

class WAdminAPI(WTemplated):

    def getVars(self):
        vars = WTemplated.getVars(self)
        akh = APIKeyHolder()
        vars['apiKeys'] = sorted(akh.getList(), key=lambda ak: ak.getUser().getFullName())
        return vars