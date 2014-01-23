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

import re
from MaKaC.common import filters, info
from MaKaC.common.ObjectHolders import ObjectHolder
from MaKaC.common.Locators import Locator
from persistent import Persistent
from MaKaC.rb_location import CrossLocationQueries

class RoomMapperHolder(ObjectHolder):
    """
    """
    idxName = "roomsMapping"
    counterName = "ROOMS_MAPPING"

    def match(self,criteria, exact=False):
        crit={}
        for f,v in criteria.items():
            crit[f]=[v]
        if crit.has_key("roommappername"):
            crit["name"] = crit["roommappername"]
        f=RoomMapperFilter(_RoomMapperFilterCriteria(crit),None)
        return f.apply(self.getList(), exact)

class RoomMapper(Persistent):

    def __init__(self, data=None):
        self._id=""
        self_name=""
        self._description=""
        self._baseMapURL=""
        self._regexps=[]
        self._placeName=""
        if data is not None:
            self.setValues(data)

    def setValues(self, d):
        self.setName(d.get("name","-- no name --"))
        self.setDescription(d.get("description",""))
        self.setBaseMapURL(d.get("url",""))
        self.setPlaceName(d.get("placeName",""))
        self.clearRegularExpressions()
        for i in d.get("regexps","").split("\r\n"):
            if i.strip() != "":
                self.addRegularExpression(i)

    def getValues(self):
        d={}
        d["name"]=self.getName()
        d["description"]=self.getDescription()
        d["mapURL"]=self.getMapURL()
        d["placeName"]=self.getPlaceName()
        return d

    def setId(self,id):
        self._id=id

    def getId(self):
        return self._id

    def getName(self):
        return self._name

    def setName(self, name):
        self._name=name

    def getDescription(self):
        return self._description

    def setDescription(self, desc):
        self._description=desc

    def getBaseMapURL(self):
        return self._baseMapURL

    def setBaseMapURL(self, url):
        self._baseMapURL=url

    def getPlaceName(self):
        return self._placeName

    def setPlaceName(self,pname):
        self._placeName=pname

    def getRegularExpressions(self):
        return self._regexps

    def addRegularExpression(self,re):
        self._regexps.append(re)

    def clearRegularExpressions(self):
        self._regexps=[]

    def applyRegularExpressions(self, roomName):
        """Returns the groupdict of attributes we have to pass to the Map URL or None if no matching"""
        for regexp in self.getRegularExpressions():
            p = re.compile(regexp)
            m = p.match(roomName)
            if m:
                return m.groupdict()
        return None

    def getMapURL(self, roomName):
        groupdict = self.applyRegularExpressions(roomName)
        if groupdict:
            return self.getBaseMapURL().format(**groupdict)
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        if minfo.getRoomBookingModuleActive():
            rooms = CrossLocationQueries.getRooms(roomName = roomName)
            rooms = [r for r in rooms if r is not None]
            if rooms and rooms[0]:
                if all(field in self.getBaseMapURL() for field in ['{building}','{floor}','{roomNr}']):
                    return self.getBaseMapURL().format(**{'building': str(rooms[0].building),'floor': rooms[0].floor,'roomNr': rooms[0].roomNr})
        return ""
    getCompleteMapURL = getMapURL

    def getLocator( self ):
        d = Locator()
        d["roomMapperId"] = self.getId()
        return d


class _RoomMapperFFBasicName(filters.FilterField):
    """
    Use when the filter is comparing basic strings
    """

    def _getBasicNameFunc(self, room_mapper):
        """
        returns the method that will provide the string value to use in the comparison
        """
        pass

    def satisfies(self, room_mapper, exact=False):
        for value in self._values:
            if value is not None and value.strip() != "":
                if value.strip() == "*":
                    return True
                if exact:
                    if self._getBasicNameFunc(room_mapper)().lower().strip() == value.lower().strip():
                        return True
                else:
                    if str(self._getBasicNameFunc(room_mapper)()).lower().find((str(value).strip().lower())) != -1:
                        return True
        return False


class _RoomMapperFFName(_RoomMapperFFBasicName):
    _id = "name"

    def _getBasicNameFunc(self, room_mapper):
        return room_mapper.getName


class _RoomMapperFFPlaceName(_RoomMapperFFBasicName):
    _id = "placename"

    def _getBasicNameFunc(self, room_mapper):
        return room_mapper.getPlaceName


class _RoomMapperFilterCriteria(filters.FilterCriteria):

    _availableFields = {"name": _RoomMapperFFName,
                        "placename": _RoomMapperFFPlaceName}

    def __init__(self, criteria={}):
        filters.FilterCriteria.__init__(self, None, criteria)

    def satisfies(self, value, exact=False):
        for field in self._fields.values():
            if not field.satisfies(value, exact):
                return False
        return True


class RoomMapperFilter(filters.SimpleFilter):
    """Performs filtering and sorting over a list of abstracts.
    """

    def apply(self,targetList, exact=False):
        """
        """
        result = []
        if self._filter:
            #self._filter.optimise()
            for item in targetList:
                if self._filter.satisfies( item, exact ):
                    result.append( item )
        else:
            result = targetList
        if self._sorting:
            if self._sorting.getField():
                result.sort( self._sorting.compare )
        return result
