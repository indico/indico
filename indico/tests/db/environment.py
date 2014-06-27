

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
from indico.modules.rb.models import *
from indico.web.flask.app import make_app
from indico.core.db.sqlalchemy.core import on_models_committed

from .data import *


class DBTest(TestCase):

    # SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_DATABASE_URI = 'postgresql:///testing'
    TESTING = True

    def create_app(self):
        app = make_app(db_setup=False)
        app.config['SQLALCHEMY_DATABASE_URI'] = self.SQLALCHEMY_DATABASE_URI
        db.init_app(app)
        configure_mappers()
        models_committed.connect(on_models_committed, app)
        return app

    def setUp(self):
        db.create_all()
        self.init_db()

    def get_without(self, d, ks=[]):
        return dict((k, v) for k, v in d.items() if k not in ks)

    def init_db(self):

        # locations
        for loc in LOCATIONS:
            location = Location(
                **self.get_without(loc, ['aspects', 'rooms', 'attributes', 'default_aspect_id', 'room_equipment'])
            )

            # aspects
            default_aspect_id = loc.get('default_aspect_id', None)
            for i, asp in enumerate(loc.get('aspects', [])):
                a = Aspect(**asp)
                location.aspects.append(a)
                if i == default_aspect_id:
                    location.default_aspect = a

            # location attributes
            for attr in loc.get('attributes', []):
                v = RoomAttribute(**self.get_without(attr, ['raw_data']))
                location.attributes.append(v)

            # location attributes
            for equip in loc.get('room_equipment', []):
                location.equipments.append(equip)

            db.session.add(location)

        transaction.commit()

        for loc in LOCATIONS:
            location = Location.query.filter_by(name=loc['name']).one()
            # rooms
            for r in loc.get('rooms', []):
                only_r = self.get_without(r, [
                    'attributes',
                    'bookable_times',
                    'equipments',
                    'nonbookable_dates',
                    'photo',
                    'reservations',
                ])
                room = Room(**only_r)

                # room attributes
                for attr in r.get('attributes', []):
                    attribute = RoomAttribute.query.filter_by(name=attr['name']).one()
                    assoc = RoomAttributeAssociation(attribute_id=attribute.id, room_id=room.id,
                                                     raw_data=attr['raw_data'])
                    room.attributes.append(assoc)

                # room equipments
                room.equipments.extend([
                    location.get_equipment_by_name(eq) for eq in r.get('equipments', [])
                ])

                # room bookable times
                room.bookable_times.extend([
                    BookableTime(**bt) for bt in r.get('bookable_times', [])
                ])

                # room nonbookabke dates
                room.nonbookable_dates.extend([
                    NonBookableDate(**nbt) for nbt in r.get('nonbookable_dates', [])
                ])

                # room photos
                room.photo = Photo(**r.get('photos', {}))

                location.rooms.append(room)

                for resv in r.get('reservations', []):
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
                        ReservationEditLog(**ed) for ed in resv.get('edit_logs', [])
                    ])

                    # reservation occurrences
                    reservation.create_occurrences(True, None)

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
            for blr in bl.get('blocked_rooms', []):
                br = BlockedRoom(**self.get_without(blr, ['room']))
                Room.getRoomByName(blr['room']).blocked_rooms.append(br)
                block.blocked_rooms.append(br)

            db.session.add(block)
        transaction.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
