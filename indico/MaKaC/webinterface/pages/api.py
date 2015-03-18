# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from MaKaC.webinterface.pages.admins import WPPersonalArea
from MaKaC.webinterface.wcomponents import WTemplated
from indico.modules.api.models.keys import APIKey
from indico.modules.api import APIMode
from indico.modules.api import settings as api_settings
from indico.web.flask.templating import get_template_module


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
        apiMode = api_settings.get('security_mode')
        vars = WTemplated.getVars(self)
        vars['avatar'] = self._avatar
        vars['apiKey'] = self._avatar.api_key
        old_keys = APIKey.find(user_id=self._avatar.id, is_active=False).order_by(APIKey.created_dt.desc()).all()
        vars['old_keys'] = old_keys
        vars['isAdmin'] = self._rh._getUser().isAdmin()
        vars['signingEnabled'] = apiMode in {APIMode.SIGNED, APIMode.ONLYKEY_SIGNED, APIMode.ALL_SIGNED}
        vars['persistentAllowed'] = api_settings.get('allow_persistent')
        tpl = get_template_module('api/_messages.html')
        vars['apiPersistentEnableAgreement'] = tpl.get_enable_persistent_msg()
        vars['apiPersistentDisableAgreement'] = tpl.get_disable_persistent_msg()
        return vars
