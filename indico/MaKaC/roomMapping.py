# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import re
from MaKaC.common import filters
from MaKaC.common.ObjectHolders import ObjectHolder
from MaKaC.common.Locators import Locator
from persistent import Persistent

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
        """Returns the attribute we have to pass to the Map URL or None if no matching"""
        for regexp in self.getRegularExpressions():
            p = re.compile(regexp)
            m=p.match(roomName)
            if m is not None:
                if len(m.groups()) == 1:
                    return m.group(1)
                elif len(m.groups()) == 0 and m.group() != "":
                    return m.group()
        return None

    def getMapURL(self, roomName):
        attr=self.applyRegularExpressions(roomName)
        if attr is not None:
            return "%s%s"%(self.getBaseMapURL(), attr)
        else:
            return ""
    getCompleteMapURL=getMapURL
        
    def getLocator( self ):
        d = Locator()
        d["roomMapperId"] = self.getId()
        return d
    
class _RoomMapperFFName(filters.FilterField):
    _id="name"

    def satisfies(self,roomMapper, exact=False):  
        for value in self._values:
            if value.strip() != "":
                if value.strip() == "*":
                    return True
                if exact:
                    if roomMapper.getName().lower().strip() == value.lower().strip():
                        return True
                else:
                    if str(roomMapper.getName()).lower().find((str(value).strip().lower()))!=-1:
                        return True
        return False


class _RoomMapperFilterCriteria(filters.FilterCriteria):
    _availableFields={"name":_RoomMapperFFName}

    def __init__(self,criteria={}):
        filters.FilterCriteria.__init__(self,None,criteria)

    def satisfies( self, value, exact=False):
        for field in self._fields.values():
            if not field.satisfies( value, exact ):
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
