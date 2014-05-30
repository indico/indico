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

from datetime import date, timedelta
from pprint import pprint

from indico.core.db import db
from indico.modules.rb.models.reservations import Reservation
from indico.tests.python.unit.indico_tests.core_tests.db_tests.data import *
from indico.tests.python.unit.indico_tests.core_tests.db_tests.db import DBTest


class TestReservation(DBTest):

    def iterReservations(self):
        for r in RESERVATIONS:
            resv = Reservation.getReservationByCreationTime(r['created_at'])
            yield r, resv
            db.session.add(resv)
        db.session.commit()

    def testGetNumberOfExcludedDays(self):
        for r, resv in self.iterReservations():
            assert len(r.get('excluded_days', [])) == resv.getNumberOfExcludedDays()
