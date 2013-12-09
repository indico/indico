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

from indico.modules.rb.models import utils
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.rooms import Room
from indico.tests.python.unit.indico_tests.core_tests.db_tests.db import DBTest


class TestUtil(DBTest):

    def testClone(self):
        original = Location.getDefaultLocation()
        cloned = utils.clone(Location, original)

        assert cloned.id != original.id
        assert cloned.name == original.name
        assert cloned.default_aspect.id == original.default_aspect.id

    def testGetDefaultValue(self):
        # TODO: defaults must be put into config
        assert utils.getDefaultValue(Room, 'capacity') == 20
        assert utils.getDefaultValue(Reservation, 'is_cancelled') == False
        with self.assertRaises(RuntimeError):
            utils.getDefaultValue(Room, 'comments')
