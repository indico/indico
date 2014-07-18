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
from sqlalchemy import func

from MaKaC.webinterface import urlHandlers
from indico.core.errors import IndicoError, FormValuesError
from indico.core.db import db
from indico.util.i18n import _
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.models.room_attributes import RoomAttribute
from indico.modules.rb.statistics import calculate_rooms_occupancy, compose_rooms_stats
from indico.modules.rb.views.admin.locations import WPRoomBookingAdmin, WPRoomBookingAdminLocation
from indico.util.string import natural_sort_key
from . import RHRoomBookingAdminBase


class RHRoomBookingAdmin(RHRoomBookingAdminBase):
    def _process(self):
        return WPRoomBookingAdmin(self).display()


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
        self._with_kpi = request.args.get('withKPI', type=bool)
        self._actionSucceeded = request.args.get('actionSucceeded', default=False, type=bool)
        location_name = request.view_args.get('locationId')
        self._location = Location.getLocationByName(location_name)
        if not self._location:
            raise IndicoError('Unknown Location: {0}'.format(location_name))

    def _process(self):
        rooms = sorted(self._location.rooms, key=lambda r: natural_sort_key(r.full_name))
        kpi = {}
        if self._with_kpi:
            kpi['occupancy'] = calculate_rooms_occupancy(self._location.rooms.all())
            kpi['total_rooms'] = self._location.rooms.count()
            kpi['active_rooms'] = self._location.rooms.filter_by(is_active=True).count()
            kpi['reservable_rooms'] = self._location.rooms.filter_by(is_reservable=True).count()
            kpi['reservable_capacity'] = (self._location.rooms.with_entities(func.sum(Room.capacity))
                                                              .filter_by(is_reservable=True).scalar())
            kpi['reservable_surface'] = (self._location.rooms.with_entities(func.sum(Room.surface_area))
                                                             .filter_by(is_reservable=True).scalar())
            kpi['booking_stats'] = compose_rooms_stats(self._location.rooms.all())
            kpi['booking_count'] = Reservation.find(Reservation.room_id.in_(r.id for r in self._location.rooms)).count()
        return WPRoomBookingAdminLocation(self,
                                          location=self._location,
                                          rooms=rooms,
                                          action_succeeded=self._actionSucceeded,
                                          possibleEquipments=self._location.getEquipmentNames(),
                                          attributes=self._location.attributes.all(),
                                          kpi=kpi).display()


class RHRoomBookingDeleteCustomAttribute(RHRoomBookingAdminBase):
    def _checkParams(self):
        name = request.view_args.get('locationId')
        self._location = Location.getLocationByName(name)
        if not self._location:
            raise IndicoError(_('Unknown Location: {0}').format(name))
        self._attr = request.args.get('removeCustomAttributeName', '')

    def _process(self):
        self._location.attributes.filter_by(name=self._attr).delete()
        db.session.add(self._location)
        self._redirect(urlHandlers.UHRoomBookingAdminLocation.getURL(self._location))


class RHRoomBookingSaveCustomAttribute(RHRoomBookingAdminBase):
    def _checkParams(self):
        name = request.view_args.get('locationId')
        self._location = Location.getLocationByName(name)
        if not self._location:
            raise IndicoError(_('Unknown Location: {0}').format(name))

        self._attrTitle = request.form.get('newCustomAttributeName', default='').strip()
        self._attrName = self._attrTitle.replace(' ', '-').lower()
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
        for attr in self._location.attributes:
            val = attr.value
            val.update({
                'is_required': request.form.get('cattr_req_{0}'.format(attr.name), '') == 'on',
                'is_hidden': request.form.get('cattr_hid_{0}'.format(attr.name), '') == 'on'
            })
            attr.value = val
        if self._attrName:
            attr = RoomAttribute(name=self._attrName, title=self._attrTitle)
            attr.value = self._value
            self._location.attributes.append(attr)

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
