# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN)
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

from flask import request

import MaKaC.webinterface.pages.admins as adminPages
import MaKaC.webinterface.urlHandlers as urlHandlers

from indico.core.db import db
from indico.modules.rb.controllers import RHRoomBookingAdminBase
from indico.modules.rb.models.locations import Location


class RHRoomBookingAdmin(RHRoomBookingAdminBase):

    def _process(self):
        return adminPages.WPRoomBookingAdmin(self).display()


class RHRoomBookingDeleteLocation(RHRoomBookingAdminBase):

    def _checkParams(self, params):
        self._locationName = request.form.get('removeLocationName', None)

    def _process(self):

        if self._locationName:
            try:
                Location.removeLocation(self._locationName)
                db.session.commit()
            except:
                db.session.rollback()
                raise # TODO: some error
        url = urlHandlers.UHRoomBookingAdmin.getURL()
        self._redirect(url)


class RHRoomBookingSaveLocation( RHRoomBookingAdminBase ):

    def _checkParams( self , params ):
        self._locationName = params["newLocationName"].strip()
        if '/' in self._locationName:
            raise FormValuesError(_('Location name may not contain slashes'))
        self._pluginClass = None
        name = params.get("pluginName","default")
        plugs = PluginLoader.getPluginsByType("RoomBooking")
        for plug in plugs:
            if pluginId(plug) == name:
                self._pluginClass = plug.roombooking.getRBClass()
        if self._pluginClass == None:
            raise MaKaCError( "%s: Cannot find requested plugin" % name )

    def _process( self ):
        if self._locationName:
            location = Location( self._locationName, self._pluginClass )
            Location.insertLocation( location )

        url = urlHandlers.UHRoomBookingAdmin.getURL()
        self._redirect( url )


class RHRoomBookingSetDefaultLocation( RHRoomBookingAdminBase ):

    def _checkParams( self , params ):
        self._defaultLocation = params["defaultLocation"]

    def _process( self ):
        Location.setDefaultLocation( self._defaultLocation )
        url = urlHandlers.UHRoomBookingAdmin.getURL()
        self._redirect( url )


class RHRoomBookingAdminLocation( RHRoomBookingAdminBase ):

    def _checkParams( self, params ):
        self._withKPI = False
        if params.get( 'withKPI' ) == 'True':
            self._withKPI = True
        name = params.get("locationId","")
        self._location = Location.parse(name)
        if str(self._location) == "None":
            raise MaKaCError( "%s: Unknown Location" % name )

        if params.get("actionSucceeded", None):
            self._actionSucceeded = True
        else:
            self._actionSucceeded = False

    def _process( self ):

        if self._withKPI:
            self._kpiAverageOccupation = RoomBase.getAverageOccupation(location=self._location.friendlyName)
            self._kpiTotalRooms = RoomBase.getNumberOfRooms(location=self._location.friendlyName)
            self._kpiActiveRooms = RoomBase.getNumberOfActiveRooms(location=self._location.friendlyName)
            self._kpiReservableRooms = RoomBase.getNumberOfReservableRooms(location=self._location.friendlyName)
            self._kpiReservableCapacity, self._kpiReservableSurface = RoomBase.getTotalSurfaceAndCapacity(location=self._location.friendlyName)

            # Bookings

            st = ReservationBase.getReservationStats(location=self._location.friendlyName)
            self._booking_stats = st
            self._totalBookings = st['liveValid'] + st['liveCancelled'] + st['liveRejected'] + st['archivalValid'] + st['archivalCancelled'] + st['archivalRejected']

        return admins.WPRoomBookingAdminLocation( self, self._location, actionSucceeded = self._actionSucceeded ).display()


class RHRoomBookingDeleteCustomAttribute( RHRoomBookingAdminBase ):  # + additional

    def _checkParams( self , params ):
        self._attr = params["removeCustomAttributeName"]
        name = params.get("locationId","")
        self._location = Location.parse(name)
        if str(self._location) == "None":
            raise MaKaCError( "%s: Unknown Location" % name )

    def _process( self ):
        self._location.factory.getCustomAttributesManager().removeAttribute( self._attr, location=self._location.friendlyName )
        url = urlHandlers.UHRoomBookingAdminLocation.getURL(self._location)
        self._redirect( url )


class RHRoomBookingSaveCustomAttribute( RHRoomBookingAdminBase ): # + additional

    def _checkParams( self , params ):
        name = params.get("locationId","")
        self._location = Location.parse(name)
        if str(self._location) == "None":
            raise MaKaCError( "%s: Unknown Location" % name )

        self._newAttr = None
        if params.get( "newCustomAttributeName" ):
            attrName = params["newCustomAttributeName"].strip()
            if attrName:
                attrIsReq = False
                if params.get( "newCustomAttributeIsRequired" ) == "on":
                    attrIsReq = True
                attrIsHidden = False
                if params.get( "newCustomAttributeIsHidden" ) == "on":
                    attrIsHidden = True
                self._newAttr = { \
                    'name': attrName,
                    'type': 'str',
                    'required': attrIsReq,
                    'hidden': attrIsHidden }

        # Set "required" for _all_ custom attributes
        manager = self._location.factory.getCustomAttributesManager()
        for ca in manager.getAttributes(location=self._location.friendlyName):
            required = hidden = False
            # Try to find in params (found => required == True)
            for k in params.iterkeys():
                if k[0:10] == "cattr_req_":
                    attrName = k[10:100].strip()
                    if attrName == ca['name']:
                        required = True
                if k[0:10] == "cattr_hid_":
                    attrName = k[10:100].strip()
                    if attrName == ca['name']:
                        hidden = True
            manager.setRequired( ca['name'], required, location=self._location.friendlyName )
            manager.setHidden( ca['name'], hidden, location=self._location.friendlyName )


class RHRoomBookingDeleteEquipment( RHRoomBookingAdminBase ):

    def _checkParams( self , params ):
        self._eq = params["removeEquipmentName"]
        name = params.get("locationId","")
        self._location = Location.parse(name)
        if str(self._location) == "None":
            raise MaKaCError( "%s: Unknown Location" % name )

    def _process( self ):
        self._location.factory.getEquipmentManager().removeEquipment( self._eq, location=self._location.friendlyName )
        url = urlHandlers.UHRoomBookingAdminLocation.getURL(self._location)
        self._redirect( url )


    def _process( self ):
        if self._newAttr:
            self._location.factory.getCustomAttributesManager().insertAttribute( self._newAttr, location=self._location.friendlyName )
        url = urlHandlers.UHRoomBookingAdminLocation.getURL(self._location)
        self._redirect( url )


class RHRoomBookingSaveEquipment( RHRoomBookingAdminBase ):

    def _checkParams( self , params ):
        self._eq = params["newEquipmentName"].strip()
        name = params.get("locationId","")
        self._location = Location.parse(name)
        if str(self._location) == "None":
            raise MaKaCError( "%s: Unknown Location" % name )

    def _process( self ):
        if self._eq:
            self._location.factory.getEquipmentManager().insertEquipment( self._eq, location=self._location.friendlyName )
        url = urlHandlers.UHRoomBookingAdminLocation.getURL(self._location)
        self._redirect( url )
