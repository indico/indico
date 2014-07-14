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

from datetime import date, timedelta, datetime
from nose.tools import assert_equal, assert_not_equal, assert_is, assert_is_not,\
    assert_in, assert_not_in, assert_true, assert_false

from indico.core.db import db
from indico.modules.rb.models.reservations import Reservation, RepeatFrequency
from indico.tests.db.data import RESERVATIONS, LOCATIONS
from indico.tests.db.environment import DBTest
from indico.tests.python.unit.util import with_context


class TestReservation(DBTest):

    def iterReservations(self):
        for r in RESERVATIONS:
            resv = Reservation.find_first(created_dt=r['created_dt'])
            yield r, resv
            db.session.add(resv)
        transaction.commit()

    def test_is_archived(self):
        for r, resv in self.iterReservations():
            if r['end_dt'] < datetime.now():
                assert_true(resv.is_archived)
            else:
                assert_false(resv.is_archived)

    def test_is_repeating(self):
        for r, resv in self.iterReservations():
            if r['repeat_frequency'] == RepeatFrequency.NEVER:
                assert_false(resv.is_repeating)
            else:
                assert_true(resv.is_repeating)

    def test_is_valid(self):
        for r, resv in self.iterReservations():
            if r['is_accepted'] and not (r['is_rejected'] or r['is_cancelled']):
                assert_true(resv.is_valid)
            else:
                assert_false(resv.is_valid)

    def test_is_pending(self):
        for r, resv in self.iterReservations():
            if not (r['is_accepted'] or r['is_rejected'] or r['is_cancelled']):
                assert_true(resv.is_pending)
            else:
                assert_false(resv.is_pending)

    def test_location_name(self):
        for r, resv in self.iterReservations():
            location_name = resv.location_name
            for loc in LOCATIONS:
                if loc['name'] == location_name:
                    assert_true(any(r in room['reservations'] for room in loc['rooms']))

    def test_repetition(self):
        for r, resv in self.iterReservations():
            assert_true(resv.repetition[0] == r['repeat_frequency'])
            assert_true(resv.repetition[1] == r['repeat_interval'])

    def test_details_url(self):
        for r, resv in self.iterReservations():
            assert_true(resv.location_name in resv.details_url)
            assert_true(str(resv.id) in resv.details_url)

    def test_status_string(self):
        for r, resv in self.iterReservations():
            if resv.is_valid:
                assert_true('Valid' in resv.status_string)
            if resv.is_cancelled:
                assert_true('Cancelled' in resv.status_string)
            if not resv.is_accepted:
                assert_true('Not confirmed' in resv.status_string)
            if resv.is_rejected:
                assert_true('Rejected' in resv.status_string)
            if resv.is_archived:
                assert_true('Archived' in resv.status_string)
            else:
                assert_true('Live' in resv.status_string)

    @with_context('database')
    def test_event(self):
        pass

    def test_get_vc_equipment(self):
        pass

    @with_context('database')
    def test_created_by_user(self):
        for r, resv in self.iterReservations():
            assert_equal(resv.created_by_user.id, self._avatar1.id)

    @with_context('database')
    def test_booked_for_user(self):
        for r, resv in self.iterReservations():
            assert_equal(resv.booked_for_user.id, self._avatar2.id)

    def test_contact_emails(self):
        for r, resv in self.iterReservations():
            for mail in resv.contact_emails:
                assert_in(mail, r['contact_email'])

    def test_get_locator(self):
        for r, resv in self.iterReservations():
            assert_equal(resv.getLocator(), {'roomLocation': resv.location_name, 'resvID': resv.id})

    @with_context('database')
    def test_can_be_modified(self):
        for r, resv in self.iterReservations():
            assert_false(resv.can_be_modified(None))
            if resv.is_rejected or resv.is_cancelled:
                assert_false(resv.can_be_modified(self._dummy))
            else:
                assert_true(resv.can_be_modified(self._dummy))
                assert_true(resv.can_be_modified(self._avatar1))
                assert_true(resv.can_be_modified(self._avatar2))
                if resv.room.is_owned_by(self._avatar3):
                    assert_true(resv.can_be_modified(self._avatar3))
                else:
                    assert_false(resv.can_be_modified(self._avatar3))

    @with_context('database')
    def test_can_be_cancelled(self):
        for r, resv in self.iterReservations():
            assert_false(resv.can_be_cancelled(None))
            assert_true(resv.can_be_cancelled(self._dummy))
            assert_true(resv.can_be_cancelled(self._avatar2))

    @with_context('database')
    def test_can_be_accepted(self):
        for r, resv in self.iterReservations():
            assert_false(resv.can_be_accepted(None))
            assert_true(resv.can_be_accepted(self._dummy))
            if resv.room.is_owned_by(self._avatar1):
                assert_true(resv.can_be_accepted(self._avatar1))
            else:
                assert_false(resv.can_be_accepted(self._avatar1))

    @with_context('database')
    def test_can_be_rejected(self):
        for r, resv in self.iterReservations():
            assert_false(resv.can_be_rejected(None))
            assert_true(resv.can_be_rejected(self._dummy))
            if resv.room.is_owned_by(self._avatar1):
                assert_true(resv.can_be_rejected(self._avatar1))
            else:
                assert_false(resv.can_be_rejected(self._avatar1))

    @with_context('database')
    def test_can_be_deleted(self):
        for r, resv in self.iterReservations():
            assert_false(resv.can_be_deleted(None))
            assert_true(resv.can_be_deleted(self._dummy))
            assert_false(resv.can_be_deleted(self._avatar1))
            assert_false(resv.can_be_deleted(self._avatar2))

    @with_context('database')
    def test_is_owned_by(self):
        for r, resv in self.iterReservations():
            assert_true(resv.is_owned_by(self._avatar1))
            assert_false(resv.is_owned_by(self._dummy))

    def testGetNumberOfExcludedDays(self):
        for r, resv in self.iterReservations():
            assert len(r.get('excluded_days', [])) == resv.getNumberOfExcludedDays()
