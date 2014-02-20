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

from datetime import date, datetime, timedelta
from pprint import pprint

from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, DAILY

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

    def testIterDays(self):
        n = 10
        our = list(utils.iterdays(date.today(), date.today() + timedelta(n)))
        lib = map(lambda dt: dt.date(), rrule(DAILY, dtstart=date.today(), count=n+1))
        assert our == lib

    def testGetWeekNumber(self):
        assert utils.getWeekNumber(date(2013, 11, 9)) == utils.getWeekNumber(date(2013, 12, 14))
        assert utils.getWeekNumber(date(2013, 4, 8)) == utils.getWeekNumber(date(2013, 5, 13))
        our = utils.getWeekNumber(date(2013, 12, 8))
        lib = utils.getWeekNumber(date(2013, 1, 5) + relativedelta(months=1))
        assert our != lib

    def testGetRandomDate(self):
        start, end = date(2013, 12, 1), date(2014, 1, 1)
        for _ in xrange(100):
            assert start <= utils.getRandomDate(start, end) <= end

    def testGetRandomDatetime(self):
        start, end = datetime(2013, 12, 1, 8), datetime(2014, 1, 1, 17)
        for _ in xrange(100):
            assert start <= utils.getRandomDatetime(start, end) <= end
