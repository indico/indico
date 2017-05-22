# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from flask import flash, redirect, request

from indico.core.db import db
from indico.core.errors import FormValuesError, IndicoError, NoReportError
from indico.modules.rb.controllers.admin import RHRoomBookingAdminBase
from indico.modules.rb.models.equipment import EquipmentType
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.room_attributes import RoomAttribute
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.statistics import calculate_rooms_occupancy, compose_rooms_stats
from indico.modules.rb.views.admin.locations import WPRoomBookingAdmin, WPRoomBookingAdminLocation
from indico.util.i18n import _
from indico.util.string import natural_sort_key
from indico.web.flask.util import url_for


class RHRoomBookingAdmin(RHRoomBookingAdminBase):
    def _process(self):
        return WPRoomBookingAdmin(self, 'rb-rooms', locations=Location.find_all()).display()


class RHRoomBookingLocationMixin:
    """Mixin that retrieves the location  or fails if there is none."""
    def _checkParams(self):
        self._location = Location.get(int(request.form['location_id']))
        if not self._location:
            raise NoReportError(u'No such location')


class RHRoomBookingDeleteLocation(RHRoomBookingLocationMixin, RHRoomBookingAdminBase):

    def _process(self):
        db.session.delete(self._location)
        flash(_(u'Location deleted'), 'success')
        return redirect(url_for('rooms_admin.roomBooking-admin'))


class RHRoomBookingSaveLocation(RHRoomBookingAdminBase):

    def _checkParams(self):
        self._locationName = request.form.get('newLocationName').strip()
        if not self._locationName:
            raise FormValuesError(_('Location name may not be empty'))
        if '/' in self._locationName:
            raise FormValuesError(_('Location name may not contain slashes'))
        if Location.find_first(name=self._locationName):
            raise FormValuesError(_('Location "{0}" already exists').format(self._locationName))

    def _process(self):
        is_default = Location.find().count() == 0
        db.session.add(Location(name=self._locationName, is_default=is_default))
        flash(_(u'Location added'), 'success')
        return redirect(url_for('rooms_admin.roomBooking-admin'))


class RHRoomBookingSetDefaultLocation(RHRoomBookingLocationMixin, RHRoomBookingAdminBase):

    def _process(self):
        self._location.set_default()
        flash(_(u'Default location changed'), 'success')
        return redirect(url_for('rooms_admin.roomBooking-admin'))


class RHRoomBookingAdminLocation(RHRoomBookingAdminBase):
    def _checkParams(self):
        self._with_kpi = request.args.get('withKPI', type=bool)
        self._actionSucceeded = request.args.get('actionSucceeded', default=False, type=bool)
        location_name = request.view_args.get('locationId')
        self._location = Location.find_first(name=location_name)
        if not self._location:
            raise IndicoError('Unknown Location: {0}'.format(location_name))

    def _process(self):
        rooms = sorted(self._location.rooms, key=lambda r: natural_sort_key(r.full_name))
        kpi = {}
        if self._with_kpi:
            kpi['occupancy'] = calculate_rooms_occupancy(self._location.rooms)
            kpi['total_rooms'] = len(self._location.rooms)
            kpi['active_rooms'] = sum(1 for room in self._location.rooms if room.is_active)
            kpi['reservable_rooms'] = sum(1 for room in self._location.rooms if room.is_reservable)
            kpi['reservable_capacity'] = sum(room.capacity or 0 for room in self._location.rooms if room.is_reservable)
            kpi['reservable_surface'] = sum(room.surface_area or 0 for room in self._location.rooms
                                            if room.is_reservable)
            kpi['booking_stats'] = compose_rooms_stats(self._location.rooms)
            kpi['booking_count'] = Reservation.find(Reservation.room.has(Room.location == self._location)).count()
        return WPRoomBookingAdminLocation(self, 'rb-rooms',
                                          location=self._location,
                                          rooms=rooms,
                                          action_succeeded=self._actionSucceeded,
                                          equipment_types=self._location.equipment_types.all(),
                                          attributes=self._location.attributes.all(),
                                          kpi=kpi).display()


class RHRoomBookingDeleteCustomAttribute(RHRoomBookingAdminBase):

    def _checkParams(self):
        name = request.view_args.get('locationId')
        self._location = Location.find_first(name=name)
        if not self._location:
            raise IndicoError(_('Unknown Location: {0}').format(name))
        self._attr = request.args.get('removeCustomAttributeName', '')

    def _process(self):
        attr = self._location.attributes.filter_by(name=self._attr).one()
        db.session.delete(attr)
        flash(_(u'Custom attribute deleted'), 'success')
        return redirect(url_for('rooms_admin.roomBooking-adminLocation', self._location))


class RHRoomBookingSaveCustomAttribute(RHRoomBookingAdminBase):

    def _checkParams(self):
        name = request.view_args.get('locationId')
        self._location = Location.find_first(name=name)
        if not self._location:
            raise IndicoError(_('Unknown Location: {0}').format(name))

        self._new_attr = None
        attr_title = request.form.get('newCustomAttributeName', default='').strip()
        if attr_title:
            attr_name = attr_title.replace(' ', '-').lower()
            if self._location.get_attribute_by_name(attr_name):
                raise FormValuesError(_('There is already an attribute named: {0}').format(attr_name))

            self._new_attr = RoomAttribute(name=attr_name, title=attr_title, type='str',
                                           is_required=request.form.get('newCustomAttributeIsRequired') == 'on',
                                           is_hidden=request.form.get('newCustomAttributeIsHidden') == 'on')

    def _process(self):
        for attr in self._location.attributes:
            attr.is_required = request.form.get('cattr_req_{}'.format(attr.name), '') == 'on'
            attr.is_hidden = request.form.get('cattr_hid_{}'.format(attr.name), '') == 'on'
        if self._new_attr:
            self._location.attributes.append(self._new_attr)
            flash(_(u'Custom attribute added'), 'success')

        flash(_(u'Custom attributes updated'), 'success')
        return redirect(url_for('rooms_admin.roomBooking-adminLocation', self._location))


class RHRoomBookingEquipmentBase(RHRoomBookingAdminBase):
    def _checkParams(self, param):
        self._eq = request.form.get(param)
        name = request.view_args.get('locationId')
        self._location = Location.find_first(name=name)
        if not self._location:
            raise IndicoError(_('Unknown Location: {0}').format(name))


class RHRoomBookingDeleteEquipment(RHRoomBookingEquipmentBase):

    def _checkParams(self):
        RHRoomBookingEquipmentBase._checkParams(self, 'removeEquipmentName')

    def _process(self):
        eq = self._location.equipment_types.filter_by(name=self._eq).one()
        db.session.delete(eq)
        flash(_(u'Equipment deleted'), 'success')
        return redirect(url_for('rooms_admin.roomBooking-adminLocation', self._location))


class RHRoomBookingSaveEquipment(RHRoomBookingEquipmentBase):

    def _checkParams(self):
        RHRoomBookingEquipmentBase._checkParams(self, 'newEquipmentName')

    def _process(self):
        if self._eq:
            self._location.equipment_types.append(EquipmentType(name=self._eq))
            flash(_(u'Equipment added'), 'success')
        return redirect(url_for('rooms_admin.roomBooking-adminLocation', self._location))
