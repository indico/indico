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

from indico.core.db import db
from indico.modules.rb.models.room_attribute_keys import RoomAttributeKey
from indico.modules.rb.models.room_attributes import RoomAttribute
from indico.modules.rb.models.room_equipments import RoomEquipment
from indico.modules.rb.models.rooms import Room
from indico.tests.python.unit.indico_tests.core_tests.db_tests.data import *
from indico.tests.python.unit.indico_tests.core_tests.db_tests.db import DBTest


class TestRoom(DBTest):

    def iterRooms(self):
        for r in ROOMS:
            room = Room.getRoomByName(r['name'])
            yield r, room
            db.session.add(room)
        db.session.commit()

    def testGetLocator(self):
        for r, room in self.iterRooms():
            l = room.getLocator()
            assert l['roomLocation'] == room.location.name
            assert l['roomID'] == room.id

    def testGetRooms(self):
        for r, room in self.iterRooms():
            pass

    def testDoesHaveLiveReservations(self):
        for r, room in self.iterRooms():
            def is_live(resv):
                return resv['start_date'] >= datetime.utcnow()
            c = len(filter(is_live, r.get('reservations', []))) > 0
            assert c == room.doesHaveLiveReservations()

    def testGetAttributeByName(self):
        rak = RoomAttributeKey(name='rak')
        room = Room.getRoomById(1)
        ra = RoomAttribute(value='test_value')
        rak.attributes.append(ra)
        room.attributes.append(ra)
        db.session.add(room)
        db.session.commit()

        assert Room.getRoomById(1).getAttributeByName('rak') == 'test_value'

    def testGetVerboseEquipment(self):
        e1 = RoomEquipment(name='eq1')
        e2 = RoomEquipment(name='eq2')

        room = Room.getRoomById(5)
        room.equipments.extend([e1, e2])
        db.session.add(room)
        db.session.commit()

        assert ','.join(['eq1', 'eq2']) == Room.getRoomById(5).getVerboseEquipment()

