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

import transaction
from flask.ext.testing import TestCase
from flask.ext.sqlalchemy import models_committed
from sqlalchemy.orm import configure_mappers

from indico.core.db import db
from indico.core.db.sqlalchemy.core import on_models_committed
from indico.modules.rb.models.aspects import Aspect
from indico.modules.rb.models.blockings import Blocking
from indico.modules.rb.models.blocked_rooms import BlockedRoom
from indico.modules.rb.models.blocking_principals import BlockingPrincipal
from indico.modules.rb.models.equipment import EquipmentType
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.reservation_edit_logs import ReservationEditLog
from indico.modules.rb.models.photos import Photo
from indico.modules.rb.models.room_attributes import RoomAttribute, RoomAttributeAssociation
from indico.modules.rb.models.room_bookable_hours import BookableHours
from indico.modules.rb.models.room_nonbookable_periods import NonBookablePeriod
from indico.modules.rb.models.rooms import Room
from indico.tests.db.data import BLOCKINGS, LOCATIONS, ROOMS, ROOM_ATTRIBUTE_ASSOCIATIONS, RESERVATIONS
from indico.tests.python.unit.util import IndicoTestCase, with_context
from indico.web.flask.app import make_app
from MaKaC.user import Avatar


class DBTest(TestCase, IndicoTestCase):

    # SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_DATABASE_URI = 'postgresql:///testing'
    TESTING = True
    _requires = ['db.DummyUser', 'db.DummyGroup']

    def create_app(self):
        app = make_app(db_setup=False)
        app.config['SQLALCHEMY_DATABASE_URI'] = self.SQLALCHEMY_DATABASE_URI
        db.init_app(app)
        configure_mappers()
        models_committed.connect(on_models_committed, app)
        return app

    def setUp(self):
        super(DBTest, self).setUp()
        self.tearDown()
        db.create_all()
        self.customise_users_and_groups()
        self.init_db()

    def get_without(self, d, ks=[]):
        return dict((k, v) for k, v in d.items() if k not in ks)

    @with_context('database')
    def customise_users_and_groups(self):

        for room in ROOMS:
            if room['name'] == 'default_room':
                room['owner_id'] = self._avatar2.id
            else:
                room['owner_id'] = self._dummy.id

        for res in RESERVATIONS:
            res['created_by_id'] = self._avatar1.id
            res['booked_for_id'] = self._avatar2.id

    @with_context('database')
    def init_db(self):

        # locations
        for loc in LOCATIONS:
            location = Location(
                **self.get_without(loc, ['aspects', 'rooms', 'attributes', 'default_aspect_id', 'equipment_types'])
            )

            # aspects
            default_aspect_id = loc['default_aspect_id']
            for i, asp in enumerate(loc['aspects']):
                a = Aspect(**asp)
                location.aspects.append(a)
                if i == default_aspect_id:
                    location.default_aspect = a

            # location attributes
            for attr in loc['attributes']:
                v = RoomAttribute(**attr)
                location.attributes.append(v)

            # location attributes
            for equip in loc['equipment_types']:
                location.equipment_types.append(EquipmentType(name=equip))

            db.session.add(location)

        transaction.commit()

        for loc in LOCATIONS:
            location = Location.query.filter_by(name=loc['name']).one()
            # rooms
            for r in loc['rooms']:
                only_r = self.get_without(r, [
                    'attributes',
                    'bookable_hours',
                    'available_equipment',
                    'nonbookable_periods',
                    'photo',
                    'reservations',
                ])
                room = Room(**only_r)

                # room attributes
                for attr in r['attributes']:
                    attribute = RoomAttribute.query.filter_by(name=attr['name']).one()
                    assoc_value = ""
                    for item in ROOM_ATTRIBUTE_ASSOCIATIONS:
                        if item["attribute"] == attr['name'] and item["room"] == room.name:
                            assoc_value = item["value"]

                    assoc = RoomAttributeAssociation(attribute_id=attribute.id, room_id=room.id, value=assoc_value)
                    room.attributes.append(assoc)

                # room equipments
                room.available_equipment.extend([
                    location.get_equipment_by_name(eq) for eq in r['available_equipment']
                ])

                # room bookable times
                room.bookable_hours.extend([
                    BookableHours(**bt) for bt in r['bookable_hours']
                ])

                # room nonbookabke dates
                room.nonbookable_periods.extend([
                    NonBookablePeriod(**nbt) for nbt in r['nonbookable_periods']
                ])

                # room photos
                room.photo = Photo(**r['photo'])

                location.rooms.append(room)

                for resv in r['reservations']:
                    only_resv = self.get_without(resv, [
                        'attributes',
                        'edit_logs',
                        'excluded_days',
                    ])
                    reservation = Reservation(**only_resv)
                    reservation.room = room

                    # TODO: re-enable when reservation atributes work (?)
                    # reservation attributes
                    # for attr in resv.get('attributes', []):
                    #     v = ReservationAttribute(**attr)
                    #     reservation.attributes.append(v)

                    # reservation edit_logs
                    reservation.edit_logs.extend([
                        ReservationEditLog(**ed) for ed in resv['edit_logs']
                    ])

                    # reservation occurrences
                    reservation.create_occurrences(True, self._dummy)

                    room.reservations.append(reservation)
            db.session.add(location)
        transaction.commit()

        # blockings
        for bl in BLOCKINGS:
            block = Blocking(**self.get_without(bl, ['allowed', 'blocked_rooms']))

            # blocking allowed list
            block.allowed.extend([BlockingPrincipal(**a)
                                  for a in bl.get('allowed', [])])

            # blocking blocked rooms
            for blr in bl['blocked_rooms']:
                br = BlockedRoom(**self.get_without(blr, ['room']))
                Room.find_first(Room.name == blr['room']).blocked_rooms.append(br)
                block.blocked_rooms.append(br)

            db.session.add(block)
        transaction.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
