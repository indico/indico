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

import unittest
from datetime import datetime, timedelta
from dateutil import rrule

from indico.modules.scheduler.tasks.periodic import PeriodicTask, TaskOccurrence


class TestPeriodicTask(unittest.TestCase):

    def testPeriodicTaskFrequency(self):
        dt = datetime(2010, 1, 1, 20, 0, 0)
        pt = PeriodicTask(rrule.MINUTELY, dtstart=dt)
        self.assertEqual(pt.getStartOn(), datetime(2010, 1, 1, 20, 0, 0))
        pt.setNextOccurrence(dateAfter=dt)
        self.assertEqual(pt.getStartOn(), datetime(2010, 1, 1, 20, 1, 0))

        pt = PeriodicTask(rrule.HOURLY, dtstart=dt)
        self.assertEqual(pt.getStartOn(), datetime(2010, 1, 1, 20, 0, 0))
        pt.setNextOccurrence(dateAfter=dt)
        self.assertEqual(pt.getStartOn(), datetime(2010, 1, 1, 21, 0, 0))

    def testPeriodicTaskNoMoreLeft(self):
        dt = datetime(2010, 1, 1, 20, 0, 0)
        # date + 1 month
        pt = PeriodicTask(rrule.YEARLY, dtstart=dt, until=dt + timedelta(days=30))
        self.assertEqual(pt.getStartOn(), datetime(2010, 1, 1, 20, 0, 0))
        pt.setNextOccurrence(dateAfter=dt)
        self.assertEqual(pt.getStartOn(), None)
        pt.setNextOccurrence(dateAfter=dt)
        self.assertEqual(pt.getStartOn(), None)

    def testPeriodicTaskOrder(self):
        dt = datetime(2010, 1, 1, 20, 0, 0)
        pt = PeriodicTask(rrule.MINUTELY, dtstart=dt)
        pt.id = 0
        pt2 = PeriodicTask(rrule.MINUTELY, dtstart=dt)
        pt2.id = 1
        for i in range(5):
            pt.addOccurrence(TaskOccurrence(pt))
            pt2.addOccurrence(TaskOccurrence(pt2))
        self.assertEqual(cmp(pt, pt2), -1)
        self.assertEqual(cmp(pt._occurrences[0], pt2), -1)
        self.assertEqual(cmp(pt._occurrences[0], pt), 1)
        self.assertEqual(cmp(pt._occurrences[0], pt._occurrences[1]), -1)
        self.assertEqual(cmp(pt._occurrences[0], pt._occurrences[0]), 0)
        self.assertEqual(cmp(pt._occurrences[0], pt2._occurrences[0]), -1)
