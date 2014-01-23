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

from indico.util.date_time import format_datetime
from indico.modules.oauth.db import ConsumerHolder, AccessTokenHolder
from indico.core.index import Catalog
from MaKaC.common.logger import Logger
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.pages.base import WPDecorated
from MaKaC.webinterface.pages.admins import WPServicesCommon, WPPersonalArea
from MaKaC.webinterface.wcomponents import WTemplated


class WPAdminOAuthConsumers(WPServicesCommon):

    def _getTabContent(self, params):
        c = WAdminOAuthConsumers()
        return c.getHTML(params)

    def _setActiveTab(self):
        self._subTabOauth.setActive()
        self._subTabOauth_Consumers.setActive()


class WAdminOAuthConsumers(WTemplated):

    def getVars(self):
        wvars = WTemplated.getVars(self)
        ch = ConsumerHolder()

        wvars['consumers'] = sorted(ch.getList(), key=lambda c: c.getName())
        return wvars


class WPAdminOAuthAuthorized(WPServicesCommon):

    def _getTabContent(self, params):
        c = WAdminOAuthAuthorized()
        return c.getHTML(params)

    def _setActiveTab(self):
        self._subTabOauth.setActive()
        self._subTabOauth_Authorized.setActive()


class WAdminOAuthAuthorized(WTemplated):

    def getVars(self):
        wvars = WTemplated.getVars(self)
        ath = AccessTokenHolder()
        wvars["formatTimestamp"] = lambda ts: format_datetime(ts, format='d/M/yyyy H:mm')
        wvars['tokens'] = sorted(ath.getList(), key=lambda t: t.getUser().getId())
        return wvars


class WPOAuthThirdPartyAuth(WPDecorated):

    def __init__(self, rh):
        WPDecorated. __init__(self, rh)

    def _getHeader(self):
        return ""

    def _getFooter(self):
        return ""

    def _getBody(self, params):
        Logger.get('oaut.authorize').info(params)
        wc = WOAuthThirdPartyAuth()
        return wc.getHTML(params)


class WOAuthThirdPartyAuth(WTemplated):

    def getVars(self):
        wvars = WTemplated.getVars(self)
        urlParams = {'userId': wvars["userId"],
                     'callback': wvars["callback"],
                     'third_party_app': wvars["third_party_app"]}

        allowURL = urlHandlers.UHOAuthAuthorizeConsumer.getURL()
        allowURL.addParams(urlParams)
        allowURL.addParam('response', 'accept')
        refuseURL = urlHandlers.UHOAuthAuthorizeConsumer.getURL()
        refuseURL.addParams(urlParams)
        refuseURL.addParam('response', 'refuse')

        wvars["allowURL"] = str(allowURL)
        wvars["refuseURL"] = str(refuseURL)

        return wvars


class WPOAuthUserThirdPartyAuth(WPPersonalArea):

    def _getTabContent(self, params):
        c = WOAuthUserThirdPartyAuth(self._avatar)
        return c.getHTML(params)

    def _setActiveTab(self):
        self._tabThirdPartyAuth.setActive()


class WOAuthUserThirdPartyAuth(WTemplated):

    def __init__(self, av):
        self._avatar = av

    def getVars(self):
        wvars = WTemplated.getVars(self)
        wvars['user'] = self._avatar
        wvars['currentUser'] = self._rh._getUser()
        wvars["tokens"] = Catalog.getIdx('user_oauth_access_token').get(self._avatar.getId(), [])
        wvars["formatTimestamp"] = lambda ts: format_datetime(ts, format='d/M/yyyy H:mm')
        return wvars
