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

import MaKaC

class FactoryCERN( object ):
    """ Creates object instances specific to CERN """

    locationName = 'CERN'

    @staticmethod
    def getName():
        return MaKaC.plugins.RoomBooking.CERN.__metadata__['name']

    @staticmethod
    def getDescription():
        return MaKaC.plugins.RoomBooking.CERN.__metadata__['description']

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
    def newRoomBlocking():
        import roomblockingCERN
        return roomblockingCERN.RoomBlockingCERN

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
