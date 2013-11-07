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

from flask.ext.testing import TestCase

from indico.core.db import db
from indico.modules.rb.models import *
from indico.tests.python.unit.indico_tests.core_tests.db_tests.data import *
from indico.web.flask.app import make_app


class DBTest(TestCase):

    # SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_DATABASE_URI = 'postgres://127.0.0.1/testing'
    TESTING = True

    def create_app(self):
        app = make_app(db_setup=False)
        db.init_app(app)
        return app

    def setUp(self):
        db.create_all()
        self.init_db()

    def get_without(self, d, ks=[]):
        return dict((k, v) for k, v in d.items() if k not in ks)

    def get_occurrences(self, r):
        pass

    def init_db(self):

        # first add attribute keys and room equipments
        db.session.add_all([LocationAttributeKey(name=k)
                            for k in LOCATION_ATTRIBUTE_KEYS])

        db.session.add_all([RoomAttributeKey(name=k)
                            for k in ROOM_ATTRIBUTE_KEYS])

        db.session.add_all([ReservationAttributeKey(name=k)
                            for k in RESERVATION_ATTRIBUTE_KEYS])

        db.session.add_all([RoomEquipment(name=k)
                            for k in ROOM_EQUIPMENTS])

        db.session.commit()

        # locations
        for loc in LOCATIONS:
            location = Location(
                **self.get_without(loc, ['aspects', 'rooms', 'attributes', 'default_aspect_id'])
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
                k = LocationAttributeKey.getKeyByName(attr['name'])
                v = LocationAttribute(**self.get_without(attr, ['name']))
                k.attributes.append(v)
                location.attributes.append(v)

            # rooms
            for r in loc.get('rooms', []):
                only_r = self.get_without(r, [
                    'attributes',
                    'bookable_times',
                    'equipments',
                    'nonbookable_dates',
                    'photos',
                    'reservations',
                ])
                room = Room(**only_r)

                # room attributes
                for attr in r.get('attributes', []):
                    k = RoomAttributeKey.getKeyByName(attr['name'])
                    v = RoomAttribute(**self.get_without(attr, ['name']))
                    k.attributes.append(v)
                    room.attributes.append(v)

                # room equipments
                room.equipments.extend([
                    RoomEquipment.getEquipmentByName(eq) for eq in r.get('equipments', [])
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
                room.photos.extend([Photo(**p) for p in r.get('photos', [])])

                # reservations
                for resv in r.get('reservations', []):
                    only_resv = self.get_without(resv, [
                        'attributes',
                        'edit_logs',
                        'excluded_days',
                    ])
                    reservation = Reservation(**only_resv)

                    # reservation excluded days
                    reservation.excluded_days.extend(resv.get('excluded_days', []))

                    # reservation attributes
                    for attr in resv.get('attributes', []):
                        k = ReservationAttributeKey.getKeyByName(attr['name'])
                        v = ReservationAttribute(**self.get_without(attr, ['name']))
                        k.attributes.append(v)
                        reservation.attributes.append(v)

                    # reservation edit_logs
                    reservation.edit_logs.extend([
                        ReservationEditLog(**ed) for ed in resv.get('edit_logs', [])
                    ])

                    # reservation notifications
                    # reservation.notifications.extend(self.get_occurrences(reservation))

                    room.reservations.append(reservation)
                location.rooms.append(room)
            db.session.add(location)
        db.session.commit()

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
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
