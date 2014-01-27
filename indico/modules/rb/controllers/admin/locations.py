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

from MaKaC.webinterface import urlHandlers

from indico.core.errors import IndicoError, FormValuesError
from indico.core.db import db
from indico.util.i18n import _

from . import RHRoomBookingAdminBase
from ...models.locations import Location
from ...models.room_attributes import RoomAttribute
from ...views.admin import locations as location_views


class RHRoomBookingAdmin(RHRoomBookingAdminBase):

    def _process(self):
        return location_views.WPRoomBookingAdmin(self).display()


class RHRoomBookingDeleteLocation(RHRoomBookingAdminBase):

    def _checkParams(self):
        self._locationName = request.form.get('removeLocationName')

    def _process(self):
        Location.removeLocationByName(self._locationName)
        self._redirect(urlHandlers.UHRoomBookingAdmin.getURL())


class RHRoomBookingSaveLocation(RHRoomBookingAdminBase):

    def _checkParams(self):
        self._locationName = request.form.get('newLocationName').strip()
        if not self._locationName:
            raise FormValuesError(_('Location name may not be empty'))
        if '/' in self._locationName:
            raise FormValuesError(_('Location name may not contain slashes'))
        if Location.getLocationByName(self._locationName):
            raise FormValuesError(_('Location "{0}" already exists').format(self._locationName))

    def _process(self):
        Location.addLocationByName(self._locationName)
        self._redirect(urlHandlers.UHRoomBookingAdmin.getURL())


class RHRoomBookingSetDefaultLocation(RHRoomBookingAdminBase):

    def _checkParams(self):
        self._defaultLocation = request.form.get('defaultLocation')

    def _process(self):
        Location.setDefaultLocation(self._defaultLocation)
        self._redirect(urlHandlers.UHRoomBookingAdmin.getURL())


class RHRoomBookingAdminLocation(RHRoomBookingAdminBase):

    def _checkParams(self):
        self._withKPI = request.args.get('withKPI', type=bool)
        self._actionSucceeded = request.args.get('actionSucceeded', default=False, type=bool)
        name = request.view_args.get('locationId')
        self._location = Location.getLocationByName(name)
        if not self._location:
            raise IndicoError(_('Unknown Location: {0}').format(name))

    def _process(self):
        # TODO
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

        return location_views.WPRoomBookingAdminLocation(self, self._location,
                                                         actionSucceeded=self._actionSucceeded).display()


class RHRoomBookingDeleteCustomAttribute(RHRoomBookingAdminBase):

    def _checkParams(self):
        name = request.view_args.get('locationId')
        self._location = Location.getLocationByName(name)
        if not self._location:
            raise IndicoError(_('Unknown Location: {0}').format(name))
        self._attr = request.args.get('removeCustomAttributeName', '')

    def _process(self):
        self._location.removeAttributeByName(self._attr)
        db.session.add(self._location)
        self._redirect(urlHandlers.UHRoomBookingAdminLocation.getURL(self._location))


class RHRoomBookingSaveCustomAttribute(RHRoomBookingAdminBase):

    def _checkParams(self):
        name = request.view_args.get('locationId')
        self._location = Location.getLocationByName(name)
        if not self._location:
            raise IndicoError(_('Unknown Location: {0}').format(name))

        self._attrName = request.form.get('newCustomAttributeName', default='').strip()
        if self._attrName:
            if self._location.getAttributeByName(self._attrName):
                raise FormValuesError(_('There is already an attribute named: {0}').format(self._attrName))

            self._value = {
                'type': 'str',
                'is_required': request.form.get('newCustomAttributeIsRequired') == 'on',
                'is_hidden': request.form.get('newCustomAttributeIsHidden') == 'on'
            }

    # TODO: update logic should be in location model
    def _process(self):
        for attr in self._location.getAttributes():
            val = attr.value
            val.update({
                'is_required': request.form.get('cattr_req_{0}'.format(attr.name), '') == 'on',
                'is_hidden': request.form.get('cattr_hid_{0}'.format(attr.name), '') == 'on'
            })
            attr.value = val
        if self._attrName:
            self._location.addAttribute(self._attrName, self._value)

        db.session.add(self._location)
        self._redirect(urlHandlers.UHRoomBookingAdminLocation.getURL(self._location))


class RHRoomBookingEquipmentBase(RHRoomBookingAdminBase):

    def _checkParams(self, param):
        self._eq = request.form.get(param)
        name = request.view_args.get('locationId')
        self._location = Location.getLocationByName(name)
        if not self._location:
            raise IndicoError(_('Unknown Location: {0}').format(name))


class RHRoomBookingDeleteEquipment(RHRoomBookingEquipmentBase):

    def _checkParams(self):
        RHRoomBookingEquipmentBase._checkParams(self, 'removeEquipmentName')

    def _process(self):
        self._location.removeEquipment(self._eq)
        db.session.add(self._location)
        self._redirect(urlHandlers.UHRoomBookingAdminLocation.getURL(self._location))


class RHRoomBookingSaveEquipment(RHRoomBookingEquipmentBase):

    def _checkParams(self):
        RHRoomBookingEquipmentBase._checkParams(self, 'newEquipmentName')

    def _process(self):
        if self._eq:
            self._location.addEquipment(self._eq)
            db.session.add(self._location)
        self._redirect(urlHandlers.UHRoomBookingAdminLocation.getURL(self._location))
