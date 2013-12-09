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

from pprint import pprint

from dictdiffer import diff

from indico.core.db import db
from indico.modules.rb.models.aspects import Aspect
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.models.utils import clone, getDefaultValue
from indico.tests.python.unit.indico_tests.core_tests.db_tests.data import *
from indico.tests.python.unit.indico_tests.core_tests.db_tests.db import DBTest


class TestLocation(DBTest):

    def iterLocations(self):
        for l in LOCATIONS:
            loc = Location.getLocationByName(l['name'])
            yield l, loc
            db.session.add(loc)
        db.session.commit()

    def compare_dict_and_object(self, d, o):
        for k, v in d.items():
            assert v == getattr(o, k)

    def testGetLocator(self):
        for l, loc in self.iterLocations():
            assert loc.getLocator()['locationId'] == l['name']

    def testGetSupportEmails(self):
        for l, loc in self.iterLocations():
            if 'support_emails' in l:
                assert loc.getSupportEmails(to_list=False) == l['support_emails']
                assert loc.getSupportEmails() == l['support_emails'].split(',')

    def testSetSupportEmails(self):
        for i, (l, loc) in enumerate(self.iterLocations()):
            loc.setSupportEmails(['a{}@example.com'.format(i), 'b{}@example.com'.format(i)])

        for i, (l, loc) in enumerate(self.iterLocations()):
            assert loc.support_emails == 'a{i}@example.com,b{i}@example.com'.format(i=i)

    def testAddSupportEmails(self):
        for l, loc in self.iterLocations():
            loc.addSupportEmails('testing@cern.ch')

        for _, loc in self.iterLocations():
            assert 'testing@cern.ch' in loc.getSupportEmails()

    def testAddSupportEmailsExisting(self):
        emails = []
        for l, loc in self.iterLocations():
            emails.append(loc.getSupportEmails())
            loc.addSupportEmails(*emails[-1][:])

        for (_, loc), e in zip(self.iterLocations(), emails):
            assert sorted(loc.getSupportEmails()) == sorted(e)

    def testDeleteSupportEmails(self):
        test_email = 'testing-experimental@cern.ch'
        for l, loc in self.iterLocations():
            loc.addSupportEmails(test_email)

        for _, loc in self.iterLocations():
            assert test_email in loc.getSupportEmails()
            loc.deleteSupportEmails(test_email)

        for _, loc in self.iterLocations():
            assert test_email not in loc.getSupportEmails()

    def testGetAspects(self):
        for l, loc in self.iterLocations():
            for aspect_dict, aspect in zip(l.get('aspects', []), loc.getAspects()):
                self.compare_dict_and_object(aspect_dict, aspect)

    def testGetDefaultAspect(self):
        for l, loc in self.iterLocations():
            if 'default_aspect_id' in l:
                self.compare_dict_and_object(ASPECTS[l['default_aspect_id']], loc.default_aspect)
            else:
                assert loc.default_aspect is None

    def testSetDefaultAspect(self):
        test_aspect_name = 'testing-aspect'
        for l, loc in self.iterLocations():
            if loc.default_aspect:
                test_aspect = clone(Aspect, loc.default_aspect)
                test_aspect.name = l['name'] + test_aspect_name
                loc.aspects.append(test_aspect)
                loc.setDefaultAspect(test_aspect)

        for _, loc in self.iterLocations():
            if loc.default_aspect:
                assert loc.default_aspect.name == (loc.name + test_aspect_name)

    def testIsMapAvailable(self):
        for l, loc in self.iterLocations():
            assert loc.isMapAvailable() == ('aspects' in l)

    def testGetRooms(self):
        pass

    def testAddRoom(self):
        pass

    def testDeleteRoom(self):
        pass

    def testGetDefaultLocation(self):
        for l, loc in self.iterLocations():
            if 'is_default' in l:
                assert loc == Location.getDefaultLocation()

    def testSetDefaultLocation(self):
        if len(LOCATIONS) < 2:
            raise RuntimeWarning('Not enough locations for tis test,'
                                 ' there should be at least 2 locations')
        else:
            old_default = Location.getDefaultLocation()
            name = None
            for l, loc in self.iterLocations():
                if not loc.is_default:
                    Location.setDefaultLocation(loc)
                    db.session.commit()
                    name = l['name']
                    self.assertTrue(loc.is_default)
                    break
            assert name == Location.getDefaultLocation().name

            # revert change to decrease dependency between tests
            Location.setDefaultLocation(old_default)
            db.session.commit()

    def testGetLocationByName(self):
        for l, loc in self.iterLocations():
            assert l['name'] == loc.name

    def testRemoveLocationByName(self):
        test_location_name = 'test_location'
        db.session.add(Location(name=test_location_name))
        db.session.commit()

        assert Location.getLocationByName(test_location_name) is not None
        Location.removeLocationByName(test_location_name)
        db.session.commit()
        assert Location.getLocationByName(test_location_name) is None

    def testAverageOccupation(self):
        pass

    def testTotalBookedTime(self):
        pass

    def testTotalBookableTime(self):
        pass

    def testGetNumberOfLocations(self):
        assert len(LOCATIONS) == Location.getNumberOfLocations()

    def testGetNumberOfRooms(self):
        for l, loc in self.iterLocations():
            assert len(l['rooms']) == loc.getNumberOfRooms()

    def testGetNumberOfActiveRooms(self):
        for l, loc in self.iterLocations():
            count_from_data = sum(r.get('is_active', True) for r in l.get('rooms', []))
            assert count_from_data == loc.getNumberOfActiveRooms()

    def testGetNumberOfReservableRooms(self):
        for l, loc in self.iterLocations():
            count_from_data = sum(r.get('is_reservable', True) for r in l.get('rooms', []))
            assert count_from_data == loc.getNumberOfReservableRooms()

    def testGetReservableRooms(self):
        for l, loc in self.iterLocations():
            rooms_from_db = sorted(map(lambda r: r.name, loc.getReservableRooms()))
            rooms_from_data = sorted([r['name'] for r in l.get('rooms', [])
                                      if r.get('is_reservable', True)])
            assert rooms_from_data == rooms_from_db

    def testGetTotalReservableCapacity(self):
        default_capacity = getDefaultValue(Room, 'capacity')

        for l, loc in self.iterLocations():
            total = sum([r.get('capacity', default_capacity)
                         for r in l.get('rooms', []) if r.get('is_reservable', True)])
            assert total == loc.getTotalReservableCapacity()

    def testGetTotalReservableSurfaceArea(self):
        for l, loc in self.iterLocations():
            total = sum([r.get('surface_area', 0)
                         for r in l.get('rooms', []) if r.get('is_reservable', True)])
            assert total == (loc.getTotalReservableSurfaceArea() or 0)

    def testGetReservationStats(self):
        pass

    def testGetBuildings(self):
        for l, loc in self.iterLocations():
            buildings = {}
            for r in l.get('rooms', []):
                k = r.get('building')
                if k in buildings:
                    buildings[k]['rooms'].append(r['name'])
                    buildings[k]['has_coordinates'] = (buildings[k]['has_coordinates'] or
                                                       bool(r.get('latitude', False) and r.get('longitude', False)))
                else:
                    buildings[k] = {
                        'number': k,
                        'title': 'Building {}'.format(k),
                        'rooms': [r['name']],
                        'has_coordinates': bool(r.get('latitude', False) and r.get('longitude', False))
                    }
            for b in loc.getBuildings():
                k = b['number']
                assert k in buildings
                assert b['has_coordinates'] == buildings[k]['has_coordinates']
                for r in b['rooms']:
                    assert r.name in buildings[k]['rooms']
