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

from persistent import Persistent

from MaKaC.common.ObjectHolders import ObjectHolder
from MaKaC.common.Locators import Locator
from MaKaC.common import filters
from MaKaC.conference import TrashCanManager


class Domain(Persistent):
    """This class represents the domains which are configured inside the system.
        A domain is a set of IP filters which given an IP can determine if it
        belongs to it or not depending on the filter application result.
    """

    def __init__( self ):
        self.id = ""
        self.name = ""
        self.description = ""
        self.filterList = []

    def getLocator( self ):
        d = Locator()
        d["domainId"] = self.getId()
        return d

    def setId( self, newId ):
        self.id = str(newId)

    def getId( self ):
        return self.id

    def setName( self, newName ):
        self.name = newName.strip()

    def getName( self ):
        return self.name

    def setDescription( self, newDescription ):
        self.description = newDescription.strip()

    def getDescription( self ):
        return self.description

    def setFilterList(self, fl):
        self.filterList = fl

    def getFilterList( self ):
        return self.filterList

    def addFilter( self, filter ):
        f = filter.strip()
        #ToDo: We have to check a filter is specified in the good format (IP)
        if f in self.filterList:
            return
        self.filterList.append(f)

    def addFiltersFromStr( self, filters ):
        """
        """
        for filter in filters.split(";"):
            self.addFilter( filter.strip() )

    def setFiltersFromStr( self, filters ):
        """
        """
        self.filterList = []
        self.addFiltersFromStr( filters )

    def removeFilter( self, filter ):
        f = filter.strip()
        if f not in self.filterList:
            return
        self.filterList.remove(f)

    def belongsTo( self, IP ):
        ip = IP.strip()
        #ToDo: check that the IP is in the correct format
        for filt in self.getFilterList():
            if ip.startswith(filt):
                return True
        return False


class _DomainFFName(filters.FilterField):
    _id="name"

    def satisfies(self, dom):
        for value in self._values:
            if str(dom.getName()).lower().find((str(value).strip().lower()))!=-1:
                return True
        return False


class _DomainFilterCriteria(filters.FilterCriteria):
    _availableFields={"name":_DomainFFName}

    def __init__(self,criteria={}):
        filters.FilterCriteria.__init__(self,None,criteria)


class DomainHolder(ObjectHolder):
    idxName = "domains"
    counterName = "DOMAINS"

    def match( self, criteria):
        """
        """
        crit={}
        for f,v in criteria.items():
            crit[f]=[v]
        f=filters.SimpleFilter(_DomainFilterCriteria(crit),None)
        return f.apply(self.getList())

    def remove(self, item):
        # METHOD HAS TO BE IMPLEMENTED...
        ObjectHolder.remove(self, item)
        TrashCanManager().add(item)

    def getLength( self ):
        return len(self.getList())

    def getBrowseIndex( self ):
        letters = []
        for domain in self.getList():
            name = domain.getName()
            if name and not name[0].lower() in letters:
                letters.append(name[0].lower())
        letters.sort()
        return letters

    def matchFirstLetter( self, letter ):
        list = []
        for domain in self.getList():
            name = domain.getName()
            if name and name[0].lower() == letter.lower():
                list.append(domain)
        return list
