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


from indico.core.db import db

from ..models.aspects import Aspect
from ..models.locations import Location
from ..models.utils import intOrDefault
from . import ServiceBase, ServiceError


class RoomBookingMapBase(ServiceBase):

    def _param(self, parameter_name):
        try:
            return self._params[parameter_name]
        except:
            raise ServiceError('ERR-RB0', 'Invalid parameter name: {0}.'.format(parameter_name))


class RoomBookingMapCreateAspect(RoomBookingMapBase):

    def _checkParams(self):
        self._location = Location.getLocationByName(self._param('location'))
        aspect_data = self._param('aspect')
        self._aspect = Aspect(
            name=aspect_data.get('name', ''),
            center_latitude=aspect_data.get('center_latitude', ''),
            center_longitude=aspect_data.get('center_longitude', ''),
            zoom_level=intOrDefault(aspect_data.get('zoom_level', '0'), default=0),
            top_left_latitude=aspect_data.get('top_left_latitude', ''),
            top_left_longitude=aspect_data.get('top_left_longitude', ''),
            bottom_right_latitude=aspect_data.get('bottom_right_latitude', ''),
            bottom_right_longitude=aspect_data.get('bottom_right_longitude', '')
        )
        self._default_on_startup = aspect_data.get('DefaultOnStartup', False)

    def _getAnswer(self):
        self._location.addAspect(self._aspect)
        if self._default_on_startup:
            self._location.default_aspect = self._aspect
        db.session.add(self._location)
        db.session.flush()
        return self._aspect.id
        # return self._location.getAspectsAsDictionary()


class RoomBookingMapUpdateAspect(RoomBookingMapBase):

    def _checkParams(self):
        self._location = Location.getLocationByName(self._param('location'))
        self._aspect = self._param('aspect')

    def _getAnswer(self):
        aspect = self._location.getAspectById(self._aspect.pop('id'))
        if aspect:
            default_on_startup = self._aspect.pop('default_on_startup')
            aspect.updateFromDictionary(self._aspect)
            if default_on_startup:
                self._location.default_aspect = aspect
            elif self._location.default_aspect.id == aspect.id:
                self._location.default_aspect = None
            db.session.add(self._location)
            db.session.flush()
        return {}
        # return self._location.getAspectsAsDictionary()


class RoomBookingMapRemoveAspect(RoomBookingMapBase):

    def _checkParams(self):
        self._location = Location.getLocationByName(self._param('location'))
        self._aspectId = self._param('aspectId')

    def _getAnswer(self):
        self._location.removeAspectById(self._aspectId)
        db.session.add(self._location)
        return {}


class RoomBookingMapListAspects(RoomBookingMapBase):

    def _checkParams(self):
        self._location = Location.getLocationByName(self._param('location'))

    def _getAnswer(self):
        return self._location.getAspectsAsDictionary()
