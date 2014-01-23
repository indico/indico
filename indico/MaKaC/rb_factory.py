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
    def newRoomBlocking():
        """Instantiates new blocking object, specific for the location"""
        return Location.getDefaultLocation().factory.newRoomBlocking()

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

