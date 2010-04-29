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

"""
Part of Room Booking Module (rb_)
Responsible: Piotr Wlodarek
"""

from rb_location import Location

class Factory( object ):
    """
    Creates objects specific to the location, according to the Factory design pattern.
    
    Use new*() methods to instantiate objects.
    """
    
    @staticmethod
    def newRoom( locationName="" ):
        """Instantiates new room object, specific for the location"""
        location = Location.parse(locationName)
        if not location:
            location = Location.getDefaultLocation()
        room = location.factory.newRoom()
        room.locationName = location.friendlyName
        return room
    
    @staticmethod
    def newReservation():
        """Instantiates new reservation object, specific for the location"""
        return Location.getDefaultLocation().factory.newReservation()
    
    @staticmethod
    def newCrbsUser():
        """Instantiates new user object, specific for the location"""
        return Location.getDefaultLocation().factory.newCrbsUser()

    @staticmethod
    def getEquipmentManager():
        """Returns equipment manager, specific for the location"""
        return Location.getDefaultLocation().factory.getEquipmentManager()

    @staticmethod
    def getDALManager():
        """Returns data access layer manager, specific for the location"""
        return  Location.getDefaultLocation().factory.getDALManager()

    @staticmethod
    def getCustomAttributesManager():
        """Returns custom attributes manager, specific for the location"""
        return  Location.getDefaultLocation().factory.getCustomAttributesManager()

