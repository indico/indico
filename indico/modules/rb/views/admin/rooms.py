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

from ...models.rooms import Room
from . import WPRoomBookingPluginAdminBase


class WPRoomBookingRoomForm(WPRoomBookingPluginAdminBase):

    _userData = ['favorite-user-list']

    def __init__(self, rh):
        self._rh = rh
        WPRoomBookingPluginAdminBase.__init__(self, rh)

    def _setActiveTab(self):
        WPRoomBookingPluginAdminBase._setActiveTab(self)
        self._subTabConfig.setActive()

    def _getTabContent(self, params):
        return WRoomBookingRoomForm(self._rh).getHTML(params)


class WRoomBookingRoomForm(WTemplated):

    def __init__(self, rh):
        self._rh = rh

    def getVars(self):
        wvars = WTemplated.getVars(self)
        wvars['is_new'] = self._rh._new

        location, room = self._rh._location, self._rh._room
        wvars['location'] = location
        wvars['room'] = room

        wvars['largePhotoPath'] = room.getLargePhotoURL()
        wvars['smallPhotoPath'] = room.getSmallPhotoURL()
        wvars['possibleEquipments'] = dict((eq.name, eq.id in self._rh._equipments)
                                            for eq in location.getEquipments())

        wvars['errors'] = self._rh._errors

        wvars['owner_name'] = getattr(room.getResponsible(), 'name', '')

        wvars['attrs'] = []
        wvars['nonBookableDates'] = self._rh._nonbookable_dates
        wvars['dailyBookablePeriods'] = self._rh._bookable_times

        return wvars
