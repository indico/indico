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

from indico.web.http_api.auth import APIKey, APIKeyHolder
from indico.web.http_api import API_MODES
from MaKaC.webinterface.rh.users import RHUserBase
from MaKaC.webinterface.rh.services import RHServicesBase
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.pages.api import WPUserAPI, WPAdminAPIOptions, WPAdminAPIKeys
from MaKaC.errors import AccessError, FormValuesError

class RHUserAPI(RHUserBase):
    def _process(self):
        p = WPUserAPI(self, self._avatar)
        return p.display()

class RHUserAPICreate(RHUserBase):
    def _checkProtection(self):
        RHUserBase._checkProtection(self)
        ak = self._avatar.getAPIKey()
        if ak and ak.isBlocked():
            raise AccessError()

    def _process(self):
        ak = self._avatar.getAPIKey()
        if not ak:
            ak = APIKey(self._avatar)
            ak.create()
        else:
            ak.newKey()
            ak.newSignKey()
        self._redirect(urlHandlers.UHUserAPI.getURL(self._avatar))

class RHUserAPIBlock(RHUserBase):
    def _checkParams(self, params):
        RHUserBase._checkParams(self, params)
        self._ak = self._avatar.getAPIKey()

    def _checkProtection(self):
        RHUserBase._checkProtection(self)
        if not self._getUser().isAdmin():
            raise AccessError()

    def _process(self):
        self._ak.setBlocked(not self._ak.isBlocked())
        self._redirect(urlHandlers.UHUserAPI.getURL(self._avatar))

class RHUserAPIDelete(RHUserBase):
    def _checkParams(self, params):
        RHUserBase._checkParams(self, params)
        self._ak = self._avatar.getAPIKey()

    def _checkProtection(self):
        RHUserBase._checkProtection(self)
        if not self._getUser().isAdmin():
            raise AccessError()

    def _process(self):
        self._ak.remove()
        self._redirect(urlHandlers.UHUserAPI.getURL(self._avatar))


class RHAdminAPIOptions(RHServicesBase):
    def _process(self):
        p = WPAdminAPIOptions(self)
        return p.display()

class RHAdminAPIOptionsSet(RHServicesBase):
    def _checkParams(self, params):
        RHServicesBase._checkParams(self, params)
        self._httpsRequired = bool(params.get('httpsRequired'))
        self._apiMode = int(params.get('apiMode'))
        try:
            self._apiCacheTTL = int(params.get('apiCacheTTL', 0))
            self._apiSignatureTTL = int(params.get('apiSignatureTTL', 0))
            if self._apiCacheTTL < 0 or self._apiSignatureTTL < 0:
                raise ValueError
        except ValueError:
            raise FormValuesError('TTLs must be positive numbers')
        if self._apiMode not in API_MODES:
            raise FormValuesError()

    def _process(self):
        self._minfo.setAPIHTTPSRequired(self._httpsRequired)
        self._minfo.setAPIMode(self._apiMode)
        self._minfo.setAPICacheTTL(self._apiCacheTTL)
        self._minfo.setAPISignatureTTL(self._apiSignatureTTL)
        self._redirect(urlHandlers.UHAdminAPIOptions.getURL())

class RHAdminAPIKeys(RHServicesBase):
    def _process(self):
        p = WPAdminAPIKeys(self)
        return p.display()