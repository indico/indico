# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.wcomponents import WTemplated

from indico.util.i18n import _

from . import WPRoomBookingPluginAdminBase


class WPRoomBookingPluginAdmin(WPRoomBookingPluginAdminBase):

    def __init__(self, rh, params):
        WPRoomBookingPluginAdminBase.__init__(self, rh)
        self._params = params

    def _setActiveTab(self):
        WPRoomBookingPluginAdminBase._setActiveTab(self)
        self._subTabMain.setActive()

    def _getTabContent(self, params):
        return WRoomBookingPluginAdmin(self._rh).getHTML(params)


class WRoomBookingPluginAdmin(WTemplated):

    def __init__(self, rh):
        self._rh = rh

    def getVars(self):
        wvars = WTemplated.getVars(self)

        if HelperMaKaCInfo.getMaKaCInfoInstance().getRoomBookingModuleActive():
            wvars['activationStatusText'] = _('Room Booking is currently active')
            wvars['activationText'] = _('Deactivate')
        else:
            wvars['activationStatusText'] = _('Room Booking is currently not active')
            wvars['activationText'] = _('Activate')
        wvars['toggleURL'] = urlHandlers.UHRoomBookingModuleActive.getURL()
        return wvars
