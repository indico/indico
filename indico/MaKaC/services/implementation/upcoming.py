# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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

import datetime

from MaKaC.services.implementation.base import ParameterManager, AdminService
from MaKaC.services.interface.rpc.common import ServiceError

from MaKaC import conference

from MaKaC.common.fossilize import fossilize
from MaKaC.fossils.modules import IObservedObjectFossil
from indico.modules import ModuleHolder


class ConfigUpcomingEventsBase(AdminService):
    def _checkParams(self):
        AdminService._checkParams(self)
        self._pm = ParameterManager(self._params)

    def _getAnswer(self):
        upcomingModule = ModuleHolder().getById("upcoming_events")

        return self._getResult(upcomingModule)


class ChangeCacheTTL(ConfigUpcomingEventsBase):
    def _checkParams(self):
        ConfigUpcomingEventsBase._checkParams(self)

        self._newTTL = self._pm.extract("value", pType=int, allowEmpty=True)

    def _getResult(self, module):
        if self._newTTL >= 0:
            module.setCacheTTL(datetime.timedelta(minutes=self._newTTL))

        return module.getCacheTTL().seconds/60

class ChangeNumberUpcomingItems(ConfigUpcomingEventsBase):
    def _checkParams(self):
        ConfigUpcomingEventsBase._checkParams(self)

        self._newNumberItems = self._pm.extract("value", pType=int, allowEmpty=True)

    def _getResult(self, module):
        if self._newNumberItems:
            module.setNumberItems(self._newNumberItems)

        return module.getNumberItems()

class GetEventCategoryList(ConfigUpcomingEventsBase):

    def _getResult(self, module):
        return fossilize(module.getObjectList(), IObservedObjectFossil);


class ObservedObjectBase(ConfigUpcomingEventsBase):
    def _checkParams(self):

        ConfigUpcomingEventsBase._checkParams(self)

        self._objType = self._pm.extract("type", pType=str, allowEmpty=False)
        self._objId = self._pm.extract("id", pType=str, allowEmpty=False)

        if self._objType == 'event':
            try:
                self._obj = conference.ConferenceHolder().getById(self._objId)
            except:
                raise ServiceError("ERR-O0", "Event '%s' does not exist" % self._objId)
        elif self._objType == 'category':
            try:
                self._obj = conference.CategoryManager().getById(self._objId)
            except:
                raise ServiceError("ERR-O1", "Category '%s' does not exist" % self._objId)
        else:
            raise ServiceError("ERR-O2", "Unknown type!")


class AddObservedObject(ObservedObjectBase):

    def _checkParams(self):
        ObservedObjectBase._checkParams(self)

        self._objWeight = self._pm.extract("weight", pType=float, allowEmpty=False)
        self._objDelta = self._pm.extract("delta", pType=int, allowEmpty=False)

    def _getResult(self, module):

        if module.hasObject(self._obj):
            raise ServiceError("ERR-O3", "Object is already in the list!")

        module.addObject(self._obj, self._objWeight, datetime.timedelta(days=self._objDelta))

        return fossilize(module.getObjectList()[-1], IObservedObjectFossil);

class RemoveObservedObject(ObservedObjectBase):

    def _getResult(self, module):
        module.removeObject(self._obj)

methodMap = {
    "admin.changeCacheTTL": ChangeCacheTTL,
    "admin.changeNumberItems": ChangeNumberUpcomingItems,
    "admin.getEventCategoryList": GetEventCategoryList,
    "admin.addObservedObject": AddObservedObject,
    "admin.removeObservedObject": RemoveObservedObject
    }
