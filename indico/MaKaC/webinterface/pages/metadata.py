# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.

"""
Base classes for pages that allow metadata to be exported
"""

from indico.web.http_api import API_MODE_SIGNED, API_MODE_ONLYKEY_SIGNED, API_MODE_ALL_SIGNED
from indico.web.http_api.util import generate_public_auth_request

import MaKaC.webinterface.wcomponents as wcomponents
from MaKaC.common import info
from indico.core.config import Config


class WICalExportBase(wcomponents.WTemplated):

    def _getIcalExportParams(self, user, url, params = {}):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        apiMode = minfo.getAPIMode()
        apiKey = user.getAPIKey() if user else None

        urls = generate_public_auth_request(apiMode, apiKey, url, params,
            minfo.isAPIPersistentAllowed() and (apiKey.isPersistentAllowed() if apiKey else False), minfo.isAPIHTTPSRequired())

        return {
            'currentUser': user,
            'icsIconURL': str(Config.getInstance().getSystemIconURL("ical_grey")),
            'apiMode': apiMode,
            'signingEnabled': apiMode in (API_MODE_SIGNED, API_MODE_ONLYKEY_SIGNED, API_MODE_ALL_SIGNED),
            'persistentAllowed': minfo.isAPIPersistentAllowed(),
            'requestURLs': urls,
            'persistentUserEnabled': apiKey.isPersistentAllowed() if apiKey else False,
            'apiActive': apiKey != None,
            'userLogged': user != None,
            'apiKeyUserAgreement': minfo.getAPIKeyUserAgreement(),
            'apiPersistentUserAgreement': minfo.getAPIPersistentUserAgreement()
        }
