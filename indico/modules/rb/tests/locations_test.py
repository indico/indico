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

from nose.tools import assert_equal, assert_not_equal, assert_is, assert_is_not,\
    assert_in, assert_not_in, assert_true, assert_false

from indico.core.db import db
from indico.modules.rb.models.aspects import Aspect
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.rooms import Room
from indico.tests.db.data import LOCATIONS
from indico.tests.db.environment import DBTest
from indico.tests.python.unit.util import with_context


class TestLocation(DBTest):
    #loc_data is used for data locations while loc is used for
    #locations retrieved from the test database.

    def iterLocations(self):
        for loc_data in LOCATIONS:
            loc = Location.find_first(Location.name == loc_data['name'])
            yield loc_data, loc
            db.session.add(loc)
        transaction.commit()

    def compare_dict_and_object(self, d, o):
        for k, v in d.items():
            assert_equal(v, getattr(o, k))

    def test_get_locator(self):
        for loc_data, loc in self.iterLocations():
            assert_equal(loc.getLocator()['locationId'], loc_data['name'])

    def test_is_map_available(self):
        for loc_data, loc in self.iterLocations():
            if 'aspects' in loc_data and loc_data['aspects']:
                assert_true(loc.is_map_available)
            else:
                assert_false(loc.is_map_available)

    def test_default_location(self):
        default_location = Location.default_location
        for loc_data, loc in self.iterLocations():
            if 'is_default' in loc_data and loc_data['is_default']:
                assert_equal(loc, default_location)
            else:
                assert_not_equal(loc, default_location)

    def test_set_default(self):
        pass

    def test_get_attribute_by_name(self):
        for loc_data, loc in self.iterLocations():
            for attr in loc_data['attributes']:
                assert_equal(loc.get_attribute_by_name(attr['name']).name, attr['name'])

    def test_get_equipment_by_name(self):
        for loc_data, loc in self.iterLocations():
            for equip in loc_data['equipment_types']:
                assert_equal(loc.get_equipment_by_name(equip).name, equip)

    def test_get_buildings(self):
        for loc_data, loc in self.iterLocations():
            buildings = {}
            for r in loc_data['rooms']:
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
            for b in loc.get_buildings():
                k = b['number']
                assert_in(k, buildings)
                for r in b['rooms']:
                    assert_in(r['name'], buildings[k]['rooms'])
