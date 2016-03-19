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

"""
Base classes for pages that allow metadata to be exported
"""

from indico.modules.api import APIMode
from indico.modules.api import settings as api_settings
from indico.web.flask.templating import get_template_module
from indico.web.http_api.util import generate_public_auth_request

import MaKaC.webinterface.wcomponents as wcomponents
from indico.core.config import Config


class WICalExportBase(wcomponents.WTemplated):

    def _getIcalExportParams(self, user, url, params=None):
        apiMode = api_settings.get('security_mode')
        apiKey = user.api_key if user else None

        urls = generate_public_auth_request(apiKey, url, params)
        tpl = get_template_module('api/_messages.html')

        return {
            'currentUser': user,
            'icsIconURL': str(Config.getInstance().getSystemIconURL("ical_grey")),
            'apiMode': apiMode,
            'signingEnabled': apiMode in {APIMode.SIGNED, APIMode.ONLYKEY_SIGNED, APIMode.ALL_SIGNED},
            'persistentAllowed': api_settings.get('allow_persistent'),
            'requestURLs': urls,
            'persistentUserEnabled': apiKey.is_persistent_allowed if apiKey else False,
            'apiActive': apiKey is not None,
            'userLogged': user is not None,
            'apiKeyUserAgreement': tpl.get_ical_api_key_msg(),
            'apiPersistentUserAgreement': tpl.get_ical_persistent_msg()
        }
