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

from MaKaC.webinterface.wcomponents import WTemplated

from indico.modules.rb.views.admin import WPRoomBookingPluginAdminBase


class WPRoomBookingRoomForm(WPRoomBookingPluginAdminBase):

    _userData = ['favorite-user-list']

    def __init__( self, rh ):
        self._rh = rh
        super(WPRoomBookingRoomForm, self).__init__(rh)

    def _setActiveTab( self ):
        super(WPRoomBookingRoomForm, self)._setActiveTab()
        self._subTabConfig.setActive()

    def _getTabContent(self, params):
        return WRoomBookingRoomForm(self._rh).getHTML(params)


class WRoomBookingRoomForm(WTemplated):

    def __init__(self, rh):
        self._rh = rh

    def getVars(self):
        wvars = super(WRoomBookingRoomForm, self).getVars()

        candRoom = self._rh._candRoom
        goodFactory = Location.parse(candRoom.locationName).factory

        wvars["Location"] = Location
        wvars["room"] = candRoom
        wvars["largePhotoPath"] = None
        wvars["smallPhotoPath"] = None
        wvars["config"] = Config.getInstance()
        wvars["possibleEquipment"] = goodFactory.getEquipmentManager().getPossibleEquipment(location=candRoom.locationName)

        wvars["showErrors"] = self._rh._showErrors
        wvars["errors"] = self._rh._errors

        wvars["insert"] = (candRoom.id == None)
        wvars["attrs"] = goodFactory.getCustomAttributesManager().getAttributes(location=candRoom.locationName)
        resp = candRoom.getResponsible()
        if resp:
            wvars["responsibleName"] = resp.getFullName()
        else:
            wvars["responsibleName"] = ""

        nbd = candRoom.getNonBookableDates()
        if len(nbd) == 0:
            from MaKaC.plugins.RoomBooking.default.room import NonBookableDate
            nbd = [NonBookableDate(None, None)]
        wvars["nonBookableDates"] = nbd

        nbp = candRoom.getDailyBookablePeriods()
        if len(nbp) == 0:
            from MaKaC.plugins.RoomBooking.default.room import DailyBookablePeriod
            nbp = [DailyBookablePeriod(None, None)]
        wvars["dailyBookablePeriods"] = nbp

        return wvars
