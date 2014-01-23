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

class Factory( object ):
    """ Creates object instances specific to this plugin """

    @staticmethod
    def getName():
        return MaKaC.plugins.RoomBooking.default.__metadata__['name']

    @staticmethod
    def getDescription():
        return MaKaC.plugins.RoomBooking.default.__metadata__.get('description')

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
    def newRoomBlocking():
        import MaKaC.plugins.RoomBooking.default.roomblocking as roomblocking
        return roomblocking.RoomBlocking

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

