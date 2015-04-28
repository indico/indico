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

import MaKaC.webinterface.rh.admins as admins
import MaKaC.webinterface.pages.admins as adminPages
import MaKaC.common.info as info
import MaKaC.webinterface.urlHandlers as urlHandlers


class RHUserManagementSwitchAuthorisedAccountCreation(admins.RHAdminBase):

    def _process(self):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        minfo.setAuthorisedAccountCreation(not minfo.getAuthorisedAccountCreation())
        self._redirect(urlHandlers.UHUserManagement.getURL())


class RHUserManagementSwitchNotifyAccountCreation(admins.RHAdminBase):

    def _process(self):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        minfo.setNotifyAccountCreation(not minfo.getNotifyAccountCreation())
        self._redirect(urlHandlers.UHUserManagement.getURL())


class RHUserManagementSwitchModerateAccountCreation(admins.RHAdminBase):

    def _process(self):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        minfo.setModerateAccountCreation(not minfo.getModerateAccountCreation())
        self._redirect(urlHandlers.UHUserManagement.getURL())


class RHUserManagement(admins.RHAdminBase):

    def _checkParams(self, params):
        admins.RHAdminBase._checkParams(self, params)
        self._params = params

    def _process(self):
        p = adminPages.WPUserManagement(self, self._params)
        return p.display()


class RHUsers(admins.RHAdminBase):

    def _checkParams(self, params):
        admins.RHAdminBase._checkParams(self, params)
        self._params = params

    def _process(self):
        p = adminPages.WPUserList(self, self._params)
        return p.display()
