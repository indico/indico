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
from operator import attrgetter

from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.webinterface.pages.admins import WPPersonalArea, WPServicesCommon
from MaKaC.webinterface.wcomponents import WTemplated
from indico.web.http_api.auth import APIKeyHolder
from indico.web.http_api import API_MODE_SIGNED, API_MODE_ONLYKEY_SIGNED, API_MODE_ALL_SIGNED


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
        minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
        apiMode = minfo.getAPIMode()
        vars = WTemplated.getVars(self)
        vars['avatar'] = self._avatar
        vars['apiKey'] = self._avatar.getAPIKey()
        vars['isAdmin'] = self._rh._getUser().isAdmin()
        vars['signingEnabled'] = apiMode in (API_MODE_SIGNED, API_MODE_ONLYKEY_SIGNED, API_MODE_ALL_SIGNED)
        vars['persistentAllowed'] = minfo.isAPIPersistentAllowed()
        vars['apiPersistentEnableAgreement'] = minfo.getAPIPersistentEnableAgreement()
        vars['apiPersistentDisableAgreement'] = minfo.getAPIPersistentDisableAgreement()
        return vars


class WPAdminAPIOptions(WPServicesCommon):

    def _getTabContent(self, params):
        c = WAdminAPIOptions()
        return c.getHTML(params)

    def _setActiveTab( self ):
        self._subTabHTTPAPI.setActive()
        self._subTabHTTPAPI_Options.setActive()

class WAdminAPIOptions(WTemplated):

    def getVars(self):
        minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
        vars = WTemplated.getVars(self)
        vars['apiMode'] = minfo.getAPIMode()
        vars['httpsRequired'] = minfo.isAPIHTTPSRequired()
        vars['persistentAllowed'] = minfo.isAPIPersistentAllowed()
        vars['apiCacheTTL'] = minfo.getAPICacheTTL()
        vars['apiSignatureTTL'] = minfo.getAPISignatureTTL()
        vars['apiPersistentEnableAgreement'] = minfo.getAPIPersistentEnableAgreement()
        vars['apiPersistentDisableAgreement'] = minfo.getAPIPersistentDisableAgreement()
        vars['apiKeyUserAgreement'] = minfo.getAPIKeyUserAgreement()
        vars['apiPersistentUserAgreement'] = minfo.getAPIPersistentUserAgreement()
        return vars


class WPAdminAPIKeys(WPServicesCommon):

    def _getTabContent(self, params):
        c = WAdminAPIKeys()
        return c.getHTML(params)

    def _setActiveTab( self ):
        self._subTabHTTPAPI.setActive()
        self._subTabHTTPAPI_Keys.setActive()

class WAdminAPIKeys(WTemplated):

    def getVars(self):
        vars = WTemplated.getVars(self)
        akh = APIKeyHolder()
        vars['apiKeys'] = sorted(akh.getList(), key=lambda ak: ak.getUser().getFullName())
        return vars
