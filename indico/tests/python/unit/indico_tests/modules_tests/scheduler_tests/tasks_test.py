# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import unittest
from datetime import datetime, timedelta
from dateutil import rrule

from indico.modules.scheduler.tasks import PeriodicTask

class TestPeriodicTask(unittest.TestCase):

    def testPeriodicTaskFrequency(self):
        dt = datetime(2010,1,1,20,0,0)
        pt = PeriodicTask(rrule.MINUTELY, dtstart = dt)
        self.assertEqual(pt.getStartOn(), datetime(2010,1,1,20,0,0))
        pt.setNextOccurrence(dateAfter = dt)
        self.assertEqual(pt.getStartOn(), datetime(2010,1,1,20,1,0))

        pt = PeriodicTask(rrule.HOURLY, dtstart = dt)
        self.assertEqual(pt.getStartOn(), datetime(2010,1,1,20,0,0))
        pt.setNextOccurrence(dateAfter = dt)
        self.assertEqual(pt.getStartOn(), datetime(2010,1,1,21,0,0))

    def testPeriodicTaskNoMoreLeft(self):
        dt = datetime(2010,1,1,20,0,0)
        # date + 1 month
        pt = PeriodicTask(rrule.YEARLY, dtstart = dt, until = dt + timedelta(days = 30))
        self.assertEqual(pt.getStartOn(), datetime(2010,1,1,20,0,0))
        pt.setNextOccurrence(dateAfter = dt)
        self.assertEqual(pt.getStartOn(), None)
        pt.setNextOccurrence(dateAfter = dt)
        self.assertEqual(pt.getStartOn(), None)
