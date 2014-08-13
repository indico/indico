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

# For now, disable Pylint
# pylint: disable-all

from indico.tests.env import *
from indico.tests.python.unit.util import IndicoTestFeature
from MaKaC.common.info import HelperMaKaCInfo
from indico.core import config as Configuration
from MaKaC.plugins.RoomBooking.CERN.dalManagerCERN import DALManagerCERN
from MaKaC.plugins.RoomBooking.CERN.initialize import initializeRoomBookingDB
from MaKaC.rb_location import Location


class RoomBooking_Feature(IndicoTestFeature):
    _requires = ['db.DummyUser', 'plugins.Plugins']

    def start(self, obj):
        super(RoomBooking_Feature, self).start(obj)

        with obj._context('database'):
            # Tell indico to use the current database for roombooking stuff
            minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
            cfg = Configuration.Config.getInstance()
            minfo.setRoomBookingDBConnectionParams(cfg.getDBConnectionParams())

            obj._ph.getById('RoomBooking').setActive(True)

            DALManagerCERN.connect()
            initializeRoomBookingDB("Universe", force=False)
            DALManagerCERN.disconnect()
            # do not use the method for it as it tries to re-create jsvars and fails
            minfo._roomBookingModuleActive = True
            DALManagerCERN.connect()

            # Create dummy rooms in obj._roomN - owners are fake1 and fake2 (r1 has f1, r2 has f2, r3 has f1, ...)
            location = Location.getDefaultLocation()
            obj._rooms = []
            for i in xrange(1, 8):
                room = location.newRoom()
                room.locationName = location.friendlyName
                room.name = 'DummyRoom%d' % i
                room.site = 'a'
                room.building = 1
                room.floor = 'b'
                room.roomNr = 'c'
                room.latitude = ''
                room.longitude = ''
                room.isActive = True
                room.isReservable = True
                room.resvsNeedConfirmation = False
                room.responsibleId = 'fake-%d' % (((i - 1) % 2) + 1)
                room.whereIsKey = 'Nowhere'
                room.telephone = '123456789'
                room.capacity = 10
                room.division = ''
                room.surfaceArea = 50
                room.comments = ''
                room.setEquipment([])
                room.setAvailableVC([])
                room.insert()
                obj._rooms.append(room)
                setattr(obj, '_room%d' % i, room)
