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

from indico.core.db import db
from indico.modules.api.models.keys import APIKey
from MaKaC.webinterface.rh.users import RHUserBase
from MaKaC.webinterface.rh.services import RHServicesBase
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.pages.api import WPUserAPI, WPAdminAPIKeys
from MaKaC.errors import AccessError


class RHUserAPI(RHUserBase):
    def _process(self):
        p = WPUserAPI(self, self._avatar)
        return p.display()


class RHUserAPICreate(RHUserBase):
    def _checkProtection(self):
        RHUserBase._checkProtection(self)
        ak = self._avatar.api_key
        if ak and ak.is_blocked:
            raise AccessError()

    def _process(self):
        old_ak = self._avatar.api_key
        ak = APIKey(user=self._avatar)
        if old_ak:
            old_ak.is_active = False
            ak.is_persistent_allowed = old_ak.is_persistent_allowed
        db.session.add(ak)
        self._redirect(urlHandlers.UHUserAPI.getURL(self._avatar))


class RHUserAPIBlock(RHUserBase):
    def _checkParams(self, params):
        RHUserBase._checkParams(self, params)

    def _checkProtection(self):
        RHUserBase._checkProtection(self)
        if not self._getUser().isAdmin():
            raise AccessError()

    def _process(self):
        ak = self._avatar.api_key
        ak.is_blocked = not ak.is_blocked
        self._redirect(urlHandlers.UHUserAPI.getURL(self._avatar))


class RHUserAPIDelete(RHUserBase):
    def _checkParams(self, params):
        RHUserBase._checkParams(self, params)

    def _checkProtection(self):
        RHUserBase._checkProtection(self)
        if not self._getUser().isAdmin():
            raise AccessError()

    def _process(self):
        self._avatar.api_key.is_active = False
        self._redirect(urlHandlers.UHUserAPI.getURL(self._avatar))


class RHAdminAPIKeys(RHServicesBase):
    def _process(self):
        p = WPAdminAPIKeys(self)
        return p.display()
