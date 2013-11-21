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

from MaKaC.accessControl import AdminList
from MaKaC.webinterface.wcomponents import WTemplated

from indico.modules.rb.views import WPRoomBookingBase


class WPRoomBookingWelcome(WPRoomBookingBase):

    def _getBody(self, params):
        return WRoomBookingWelcome().getHTML(params)


class WRoomBookingWelcome(WTemplated):

    def __init__(self):
        self.__adminList = AdminList.getInstance()

    def getVars(self):
        return WTemplated.getVars(self)


class WRoomBookingChooseEvent(WTemplated):

    def __init__(self, rh):
        self._rh = rh

    def getVars(self):
        wvars = super(WRoomBookingChooseEvent, self).getVars()

        wvars["conference"] = self._rh._conf
        wvars["contributions"] = [c for c in self._rh._conf.getContributionList() if c.getStartDate()]

        return wvars
