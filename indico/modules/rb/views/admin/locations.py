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

from indico.modules.rb.models.location_attribute_keys import LocationAttributeKey
from indico.modules.rb.models.locations import Location
from indico.modules.rb.views.admin import WPRoomBookingPluginAdminBase
from indico.modules.rb.views.utils import makePercentageString


class WPRoomBookingAdmin(WPRoomBookingPluginAdminBase):

    def __init__(self, rh):
        self._rh = rh
        super(WPRoomBookingAdmin, self).__init__(rh)

    def _setActiveTab(self):
        self._subTabConfig.setActive()

    def _getTabContent(self, params):
        return WRoomBookingAdmin(self._rh).getHTML(params)


class WRoomBookingAdmin(WTemplated):

    def __init__(self, rh):
        self._rh = rh

    def getVars(self):
        wvars = super(WRoomBookingAdmin, self).getVars()
        wvars['locations'] = Location.getAllLocations()
        defaultLocation = Location.getDefaultLocation()
        wvars['defaultLocationName'] = defaultLocation.name if defaultLocation else None

        return wvars


class WPRoomBookingAdminLocation(WPRoomBookingPluginAdminBase):

    def __init__(self, rh, location, actionSucceeded=False):
        self._rh = rh
        self._location = location
        self._actionSucceeded = actionSucceeded
        super(WPRoomBookingAdminLocation, self).__init__(rh)

    def _setActiveTab(self):
        self._subTabConfig.setActive()

    def _getTabContent(self, params):
        wc = WRoomBookingAdminLocation(self._rh, self._location)
        params['actionSucceeded'] = self._actionSucceeded
        return wc.getHTML(params)


class WRoomBookingAdminLocation(WTemplated):

    def __init__(self, rh, location):
        self._rh = rh
        self._location = location

    def getVars(self):
        wvars = super(WRoomBookingAdminLocation, self).getVars()
        wvars["location"] = self._location
        wvars["possibleEquipment"] = LocationAttributeKey.getAllAttributeKeys()
        wvars['AttsManager'] = None
        # wvars["AttsManager"] = self._location.factory.getCustomAttributesManager()

        # Rooms
        # rooms = self._location.factory.newRoom().getRooms(location=self._location.friendlyName)
        # rooms.sort()
        wvars["Rooms"] = self._location.getAllRoomsSortedByFullNames()

        rh = self._rh

        wvars["withKPI"] = rh._withKPI

        if rh._withKPI:
            wvars["kpiAverageOccupation"] = makePercentageString(rh._kpiAverageOccupation)

            wvars["kpiTotalRooms"] = rh._kpiTotalRooms
            wvars["kpiActiveRooms"] = rh._kpiActiveRooms
            wvars["kpiReservableRooms"] = rh._kpiReservableRooms

            wvars["kpiReservableCapacity"] = rh._kpiReservableCapacity
            wvars["kpiReservableSurface"] = rh._kpiReservableSurface

            # Bookings

            wvars["kbiTotalBookings"] = rh._totalBookings

            # Next 9 KPIs
            wvars["stats"] = rh._booking_stats

        return wvars
