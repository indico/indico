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

from MaKaC.common.logger import Logger
from MaKaC.errors import MaKaCError, FormValuesError
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.pages import admins as adminPages

from indico.core.db import db
from indico.modules.rb.controllers import RHRoomBookingAdminBase
from indico.modules.rb.models.locations import Location


logger = Logger.get('requestHandler')


class RHRoomBookingAdmin(RHRoomBookingAdminBase):

    def _process(self):
        return adminPages.WPRoomBookingAdmin(self).display()


class RHRoomBookingDeleteLocation(RHRoomBookingAdminBase):

    def _checkParams(self):
        self._locationName = request.form.get('removeLocationName')

    def _process(self):
        if self._locationName:
            try:
                db.session.remove(Location.getLocationByName(self._locationName))
                db.session.commit()
            except:
                db.session.rollback()
                logger.warning("Location couldn't be deleted! (Request {})".format(request))
                # TODO: raise
        self._redirect(urlHandlers.UHRoomBookingAdmin.getURL())


class RHRoomBookingSaveLocation(RHRoomBookingAdminBase):

    def _checkParams(self):
        self._locationName = request.form.get('newLocationName').strip()
        if '/' in self._locationName:
            raise FormValuesError(_('Location name may not contain slashes'))

    def _process(self):
        if self._locationName:
            try:
                db.session.add(Location(self._locationName))
                db.session.commit()
            except:
                db.session.rollback()
                logger.warning("Location couldn't be saved! (Request {})".format(request))
                # TODO: raise
        self._redirect(urlHandlers.UHRoomBookingAdmin.getURL())


class RHRoomBookingSetDefaultLocation(RHRoomBookingAdminBase):

    def _checkParams(self):
        self._defaultLocation = request.form.get('defaultLocation')

    def _process(self):
        try:
            Location.setDefaultLocation(self._defaultLocation)
            db.session.commit()
        except:
            db.session.rollback()
            logger.warning("Default Location couldn't be set! (Request {})".format(request))
            # TODO: raise
        self._redirect(urlHandlers.UHRoomBookingAdmin.getURL())


class RHRoomBookingAdminLocation(RHRoomBookingAdminBase):

    def _checkParams(self):
        self._withKPI = request.args.get('withKPI') == 'True'
        self._actionSucceeded = request.args.get('actionSucceeded', default=False, type=bool)
        name = request.args.get('locationId')
        try:
            # location_name | location_id
            location_id = int(name.split('|')[1])
            self._location = Location.getLocationById(location_id)
        except:
            raise MaKaCError(_("{}: Unknown Location".format(name)))

    def _process(self):
        if self._withKPI:
            self._kpiAverageOccupation = self._location.getAverageOccupation()
            self._kpiTotalRooms = self._location.getNumberOfRooms()
            self._kpiActiveRooms = self._location.getNumberOfActiveRooms()
            self._kpiReservableRooms = self._location.getNumberOfReservableRooms()
            self._kpiReservableCapacity = self._location.getTotalReservableCapacity()
            self._kpiReservableSurface = self._location.getTotalReservableSurface()

            # Bookings
            st = self._location.getReservationStats()
            self._booking_stats = st
            self._totalBookings = sum(map(lambda k, v: v, st.iteritems()))

        return adminPages.WPRoomBookingAdminLocation(self, self._location,
                                                     actionSucceeded=self._actionSucceeded).display()


class RHRoomBookingDeleteCustomAttribute(RHRoomBookingAdminBase):

    def _checkParams(self):
        self._attr = request.args.get('removeCustomAttributeName')
        name = request.args.get('locationId')
        try:
            # location_name | location_id
            location_id = int(name.split('|')[1])
            self._location = Location.getLocationById(location_id)
        except:
            raise MaKaCError(_("{}: Unknown Location".format(name)))

    def _process(self):
        try:
            self._location.removeAttribute(self._attr)
            db.session.commit()
        except:
            db.session.rollback()
            logger.warning("Location attribute couldn't be removed! (Request {})".format(request))
            # TODO: raise
        self._redirect(urlHandlers.UHRoomBookingAdminLocation.getURL(self._location))


class RHRoomBookingSaveCustomAttribute(RHRoomBookingAdminBase):

    def _checkParams(self):
        name = request.args.get('locationId')
        try:
            # location_name | location_id
            location_id = int(name.split('|')[1])
            self._location = Location.getLocationById(location_id)
        except:
            raise MaKaCError(_("{}: Unknown Location".format(name)))

        self._newAttr = None
        attrName = request.form.get('newCustomAttributeName').strip()
        if attrName:
            self._newAttr = {
                'name': attrName,
                'type': 'str',
                'required': request.form.get('newCustomAttributeIsRequired') == 'on',
                'hidden': request.form.get('newCustomAttributeIsHidden') == 'on'
            }

        # Set "required" for _all_ custom attributes
        for attr in self._location.getAttributeNames():
            required = hidden = False
            # Try to find in params (found => required == True)
            for k in request.form.iterkeys():
                if k[0:10] == "cattr_req_":
                    attrName = k[10:100].strip()
                    if attrName == attr.name:
                        attr.required = True
                elif k[0:10] == "cattr_hid_":
                    attrName = k[10:100].strip()
                    if attrName == attr.name:
                        hidden = True

            attr.setRequired(required)
            attr.setHidden(hidden)
            db.session.add(attr)

        try:
            db.session.commit()
        except:
            db.session.rollback()
            logger.warning("Location attribute couldn't be set for required/hidden! "
                           "(Request {})".format(request))
            # TODO: raise


# TODO
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


# TODO
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
