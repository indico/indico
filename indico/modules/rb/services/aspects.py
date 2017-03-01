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

from indico.core.db import db
from indico.modules.rb.models.aspects import Aspect
from indico.modules.rb.models.locations import Location
from indico.legacy.services.implementation.base import ServiceBase
from indico.legacy.services.interface.rpc.common import ServiceError


class RoomBookingMapBase(ServiceBase):
    UNICODE_PARAMS = True

    def _param(self, parameter_name):
        try:
            return self._params[parameter_name]
        except:
            raise ServiceError('ERR-RB0', 'Invalid parameter name: {0}.'.format(parameter_name))


class RoomBookingMapCreateAspect(RoomBookingMapBase):
    def _checkParams(self):
        self._location = Location.find_first(name=self._param('location'))
        aspect_data = self._param('aspect')
        try:
            zoom_level = int(aspect_data.get('zoom_level', '0'))
        except ValueError:
            zoom_level = 0
        self._aspect = Aspect(
            name=aspect_data.get('name', ''),
            center_latitude=aspect_data.get('center_latitude', ''),
            center_longitude=aspect_data.get('center_longitude', ''),
            zoom_level=zoom_level,
            top_left_latitude=aspect_data.get('top_left_latitude', ''),
            top_left_longitude=aspect_data.get('top_left_longitude', ''),
            bottom_right_latitude=aspect_data.get('bottom_right_latitude', ''),
            bottom_right_longitude=aspect_data.get('bottom_right_longitude', '')
        )
        self._default_on_startup = aspect_data.get('DefaultOnStartup', False)

    def _getAnswer(self):
        self._location.aspects.append(self._aspect)
        if self._default_on_startup:
            self._location.default_aspect = self._aspect
        db.session.flush()
        return self._aspect.id


class RoomBookingMapUpdateAspect(RoomBookingMapBase):
    def _checkParams(self):
        self._location = Location.find_first(name=self._param('location'))
        self._aspect = self._param('aspect')

    def _getAnswer(self):
        aspect = self._location.aspects.filter_by(id=self._aspect.pop('id')).first()
        if aspect:
            default_on_startup = self._aspect.pop('default_on_startup')
            for k, v in self._aspect.iteritems():
                setattr(aspect, k, v)
            if default_on_startup:
                self._location.default_aspect = aspect
            elif self._location.default_aspect.id == aspect.id:
                self._location.default_aspect = None
            db.session.flush()
        return {}


class RoomBookingMapRemoveAspect(RoomBookingMapBase):
    def _checkParams(self):
        self._location = Location.find_first(name=self._param('location'))
        self._aspectId = self._param('aspectId')

    def _getAnswer(self):
        self._location.aspects.filter_by(id=self._aspectId).delete()
        return {}


class RoomBookingMapListAspects(RoomBookingMapBase):
    def _checkParams(self):
        self._location = Location.find_first(name=self._param('location'))

    def _getAnswer(self):
        return [a.to_serializable() for a in self._location.aspects]
