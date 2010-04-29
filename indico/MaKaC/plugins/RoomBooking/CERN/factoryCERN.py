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

class FactoryCERN( object ):
    """ Creates object instances specific to CERN """

    locationName = 'CERN'

    @staticmethod
    def getName():
        return MaKaC.plugins.RoomBooking.CERN.pluginName
        
    @staticmethod
    def getDescription():
        return MaKaC.plugins.RoomBooking.CERN.pluginDescription
    
    @staticmethod
    def newRoom( locationName = "" ):
        import roomCERN
        newRoom = roomCERN.RoomCERN()
        newRoom.locationName = locationName
        return newRoom
    
    @staticmethod
    def newReservation():
        import reservationCERN
        return reservationCERN.ReservationCERN()
    
    @staticmethod
    def newCrbsUser():
        import crbsUserCERN
        return crbsUserCERN.CrbsUserCERN()

    @staticmethod
    def getEquipmentManager():
        import equipmentManagerCERN
        return equipmentManagerCERN.EquipmentManagerCERN()

    @staticmethod
    def getDALManager():
        import dalManagerCERN
        return dalManagerCERN.DALManagerCERN()

    @staticmethod
    def getCustomAttributesManager():
        import customAttributesManagerCERN as camc
        return camc.CustomAttributesManagerCERN()

