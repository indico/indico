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

import MaKaC

class Factory( object ):
    """ Creates object instances specific to this plugin """

    @staticmethod
    def getName():
        return MaKaC.plugins.RoomBooking.default.pluginName
        
    @staticmethod
    def getDescription():
        return MaKaC.plugins.RoomBooking.default.pluginDescription
    
    @staticmethod
    def newRoom( locationName = "" ):
        import MaKaC.plugins.RoomBooking.default.room as room
        newRoom = room.Room()
        newRoom.locationName = locationName
        return newRoom
    
    @staticmethod
    def newReservation():
        import MaKaC.plugins.RoomBooking.default.reservation as reservation
        return reservation.Reservation()
    
    @staticmethod
    def getEquipmentManager():
        import MaKaC.plugins.RoomBooking.default.equipmentManager as equipmentManager
        return equipmentManager.EquipmentManager()

    @staticmethod
    def getDALManager():
        import MaKaC.plugins.RoomBooking.default.dalManager as dalManager
        return dalManager.DALManager()

    @staticmethod
    def getCustomAttributesManager():
        import MaKaC.plugins.RoomBooking.default.customAttributesManager as cam
        return cam.CustomAttributesManager()

