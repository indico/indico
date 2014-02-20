# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

from datetime import datetime
from pprint import pprint

import transaction

from indico.core.db import db
from indico.modules.rb.models.room_attributes import RoomAttribute
from indico.modules.rb.models.room_equipments import RoomEquipment
from indico.modules.rb.models.rooms import Room
from ..data import *
from ..db import DBTest
from ..util import diff


class TestRoom(DBTest):

    def iterRooms(self):
        for r in ROOMS:
            room = Room.getRoomByName(r['name'])
            yield r, room
            db.session.add(room)
        transaction.commit()

    def testGetLocator(self):
        for r, room in self.iterRooms():
            l = room.getLocator()
            assert l['roomLocation'] == room.location.name
            assert l['roomID'] == room.id

    def testGetRooms(self):
        for r, room in self.iterRooms():
            assert diff(r, room)

    def testDoesHaveLiveReservations(self):
        for r, room in self.iterRooms():
            def is_live(resv):
                return resv['start_date'] >= datetime.utcnow()
            c = len(filter(is_live, r.get('reservations', []))) > 0
            assert c == room.doesHaveLiveReservations()

    def testGetAttributeByName(self):
        for r, room in self.iterRooms():
            for attr in r.get('attributes', []):
                print room.getAttributeByName(attr['name'])
                # assert attr['name'] == room.getAttributeByName(attr['name']).name

    def testGetCollisions(self):
        for r, room in self.iterRooms():
            assert r.get('excluded_days') == room.getCollisions()

    def testGetReservationStats(self):
        for r, room in self.iterRooms():
            print room.getReservationStats()

    def testGetBookableTimes(self):
        for r, room in self.iterRooms():
            assert r.get('bookable_times', []) == map(lambda b: b.toDict(), room.getBookableTimes())

    def testGetTotalBookableTime(self):
        for r, room in self.iterRooms():
            pprint(room.getTotalBookableTime())
            print

    def testGetTotalBookedTime(self):
        for r, room in self.iterRooms():
            pprint(room.getTotalBookedTime())

    def testGetAverageOccupation(self):
        for r, room in self.iterRooms():
            pprint(room.getAverageOccupation(datetime(2012, 1, 1), datetime(2015, 1, 1)))

    def testGetVerboseEquipment(self):
        e1 = RoomEquipment(name='eq1')
        e2 = RoomEquipment(name='eq2')

        room = Room.getRoomById(5)
        room.equipments.extend([e1, e2])
        db.session.add(room)
        db.session.commit()

        assert ','.join(['eq1', 'eq2']) == Room.getRoomById(5).getVerboseEquipment()
