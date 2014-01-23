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

from ZODB import FileStorage, DB
from ZODB.DB import DB, transaction
from ZODB.PersistentMapping import PersistentMapping
from persistent import Persistent

from MaKaC.plugins.RoomBooking.default.factory import Factory
from MaKaC.rb_equipmentManager import EquipmentManagerBase

# Branch name in ZODB root
# DICTIONARY of lists of possible equipment.
# Indexed by location name.
_EQUIPMENT_LIST = 'EquipmentList'

class EquipmentManager( EquipmentManagerBase ):
    """ ZODB specific implementation """

    @staticmethod
    def getRoot():
        return Factory.getDALManager().getRoot(_EQUIPMENT_LIST)

    @staticmethod
    def getPossibleEquipment( *args, **kwargs ):
        from MaKaC.rb_location import Location
        location = kwargs.get( 'location', Location.getDefaultLocation().friendlyName )

        lst = EquipmentManager.getRoot()
        if lst.get( location ) == None:
            lst[location] = []
            Factory.getDALManager().getRoot()[_EQUIPMENT_LIST] = lst
        return lst[location]

    @staticmethod
    def setPossibleEquipment( equipmentList, *args, **kwargs ):
        from MaKaC.rb_location import Location
        location = kwargs.get( 'location', Location.getDefaultLocation().friendlyName )

        lst = EquipmentManager.getRoot()
        lst[location] = equipmentList
        Factory.getDALManager().getRoot()[_EQUIPMENT_LIST] = lst     # Force update

    @staticmethod
    def insertEquipment( equipmentName, *args, **kwargs ):
        from MaKaC.rb_location import Location
        location = kwargs.get( 'location', Location.getDefaultLocation().friendlyName )

        lst = EquipmentManager.getRoot()
        if lst.get( location ) == None:
            lst[location] = []
        lst[location].append( equipmentName )
        Factory.getDALManager().getRoot()[_EQUIPMENT_LIST] = lst

    @staticmethod
    def removeEquipment( equipmentName, *args, **kwargs ):
        from MaKaC.rb_location import Location
        location = kwargs.get( 'location', Location.getDefaultLocation().friendlyName )

        lst = EquipmentManager.getRoot()
        lst[location].remove( equipmentName )
        Factory.getDALManager().getRoot()[_EQUIPMENT_LIST] = lst

    @staticmethod
    def removalIsPossible( equipmentName, *args, **kwargs ):
        """ Checks whether any room has specified equipment.
        If so, returns false.
        Else returns true. """
        pass

