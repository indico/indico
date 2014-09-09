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
## along with Indico; if not, see <http://www.gnu.org/licenses/>.

from datetime import datetime

import pytest
from dateutil.relativedelta import relativedelta

from indico.modules.rb.models.reservations import Reservation, RepeatFrequency

pytest_plugins = 'indico.modules.rb.testing.fixtures'


# ======================================================================================================================
# Hybrid property tests
# ======================================================================================================================


@pytest.mark.parametrize(('days_delta', 'expected'), (
    (-1, True),   # Reservation in the past
    (1,  False),  # Reservation in the future
    (0,  False),   # Reservation in course
))
def test_is_archived(create_reservation, days_delta, expected):
    start_dt = datetime.now() + relativedelta(days=days_delta, hours=-1)
    end_dt = datetime.now() + relativedelta(days=days_delta, hours=+1)
    reservation = create_reservation(start_dt=start_dt, end_dt=end_dt)
    assert reservation.is_archived == expected


@pytest.mark.parametrize(('is_accepted', 'is_rejected', 'is_cancelled', 'expected'), (
    (True,  True,  True,  False),
    (True,  True,  False, False),
    (True,  False, True,  False),
    (True,  False, False, False),
    (False, True,  True,  False),
    (False, True,  False, False),
    (False, False, True,  False),
    (False, False, False, True),
))
def test_is_pending(create_reservation, is_accepted, is_rejected, is_cancelled, expected):
    reservation = create_reservation(is_accepted=is_accepted, is_rejected=is_rejected, is_cancelled=is_cancelled)
    assert reservation.is_pending == expected
    assert Reservation.find_first(is_pending=expected) == reservation


@pytest.mark.parametrize(('repeat_frequency', 'expected'), (
    (RepeatFrequency.NEVER, False),
    (RepeatFrequency.DAY,   True),
    (RepeatFrequency.WEEK,  True),
    (RepeatFrequency.MONTH, True),
    (RepeatFrequency.YEAR,  True),
))
def test_is_repeating(create_reservation, repeat_frequency, expected):
    reservation = create_reservation(repeat_frequency=repeat_frequency)
    assert reservation.is_repeating == expected


@pytest.mark.parametrize(('is_accepted', 'is_rejected', 'is_cancelled', 'expected'), (
    (True,  True,  True,  False),
    (True,  True,  False, False),
    (True,  False, True,  False),
    (True,  False, False, True),
    (False, True,  True,  False),
    (False, True,  False, False),
    (False, False, True,  False),
    (False, False, False, False),
))
def test_is_valid(create_reservation, is_accepted, is_rejected, is_cancelled, expected):
    reservation = create_reservation(is_accepted=is_accepted, is_rejected=is_rejected, is_cancelled=is_cancelled)
    assert reservation.is_valid == expected
    assert Reservation.find_first(is_valid=expected) == reservation


# ======================================================================================================================
# Property tests
# ======================================================================================================================


def test_booked_for_user(dummy_reservation, dummy_user):
    assert dummy_reservation.booked_for_user == dummy_user


def test_booked_for_user_after_change(dummy_reservation, create_user):
    other_user = create_user('other')
    dummy_reservation.booked_for_user = other_user
    assert dummy_reservation.booked_for_user == other_user
    assert dummy_reservation.booked_for_id == other_user.id
    assert dummy_reservation.booked_for_name == other_user.getFullName()


def test_booked_for_user_with_no_id(dummy_reservation):
    dummy_reservation.booked_for_id = None
    assert dummy_reservation.booked_for_user is None


def test_booked_for_user_email(dummy_reservation, dummy_user):
    assert dummy_reservation.booked_for_user_email == dummy_user.email


def test_booked_for_user_email_after_change(dummy_reservation, dummy_user, create_user):
    dummy_user.email = 'new.email@example.com'
    assert dummy_reservation.booked_for_user_email == dummy_user.email
    other_user = create_user('other')
    dummy_reservation.booked_for_user = other_user
    assert dummy_reservation.booked_for_user_email == other_user.email


def test_booked_for_user_email_with_no_id(dummy_reservation):
    dummy_reservation.booked_for_id = None
    assert dummy_reservation.booked_for_user_email is None


@pytest.mark.parametrize(('emails', 'expected'), (
    ('',             set()),
    ('a@a.a',        {'a@a.a'}),
    ('a@a.a, b@b.b', {'a@a.a', 'b@b.b'}),
    ('b@b.b, b@b.b', {'b@b.b'}),
    (' c@c.c',       {'c@c.c'}),
))
def test_contact_emails(create_reservation, emails, expected):
    reservation = create_reservation(contact_email=emails)
    assert reservation.contact_emails == expected


def test_created_by_user(dummy_reservation, dummy_user):
    assert dummy_reservation.created_by_user == dummy_user


def test_created_by_user_after_change(dummy_reservation, create_user):
    other_user = create_user('other')
    dummy_reservation.created_by_user = other_user
    assert dummy_reservation.created_by_user == other_user
    assert dummy_reservation.created_by_id == other_user.id


def test_created_by_user_with_no_id(dummy_reservation):
    dummy_reservation.created_by_id = None
    assert dummy_reservation.created_by_user is None


def test_details_url(dummy_reservation):
    dummy_reservation.details_url


def test_event(dummy_reservation, dummy_event):
    dummy_reservation.event = dummy_event
    assert dummy_reservation.event.id == dummy_event.id
    assert dummy_reservation.event == dummy_event
    dummy_reservation.event = None
    assert dummy_reservation.event is None


def test_location_name(dummy_reservation, dummy_location):
    assert dummy_location.name == dummy_reservation.location_name


def test_repetition(dummy_reservation):
    assert (dummy_reservation.repeat_frequency, dummy_reservation.repeat_interval) == dummy_reservation.repetition


@pytest.mark.parametrize(('is_accepted', 'is_rejected', 'is_cancelled', 'is_archived', 'expected'), (
    (True,  True,  True,  True,  'Cancelled, Rejected, Archived'),
    (True,  True,  True,  False, 'Cancelled, Rejected, Live'),
    (True,  True,  False, True,  'Rejected, Archived'),
    (True,  True,  False, False, 'Rejected, Live'),
    (True,  False, True,  True,  'Cancelled, Archived'),
    (True,  False, True,  False, 'Cancelled, Live'),
    (True,  False, False, True,  'Valid, Archived'),
    (True,  False, False, False, 'Valid, Live'),
    (False, True,  True,  True,  'Cancelled, Rejected, Not confirmed, Archived'),
    (False, True,  True,  False, 'Cancelled, Rejected, Not confirmed, Live'),
    (False, True,  False, True,  'Rejected, Not confirmed, Archived'),
    (False, True,  False, False, 'Rejected, Not confirmed, Live'),
    (False, False, True,  True,  'Cancelled, Not confirmed, Archived'),
    (False, False, True,  False, 'Cancelled, Not confirmed, Live'),
    (False, False, False, True,  'Not confirmed, Archived'),
    (False, False, False, False, 'Not confirmed, Live'),
))
def test_status_string(create_reservation, is_accepted, is_rejected, is_cancelled, is_archived, expected):
    params = {'is_accepted': is_accepted, 'is_rejected': is_rejected, 'is_cancelled': is_cancelled}
    if is_archived:
        params['start_dt'] = datetime.now() + relativedelta(days=-1, hours=-1)
        params['end_dt'] = datetime.now() + relativedelta(days=-1, hours=+1)
    else:
        params['start_dt'] = datetime.now() + relativedelta(days=1, hours=1)
        params['end_dt'] = datetime.now() + relativedelta(days=1, hours=2)
    reservation = create_reservation(**params)
    assert str(reservation.status_string) == expected


# ======================================================================================================================
# staticmethod tests
# ======================================================================================================================


# ======================================================================================================================
# method tests
# ======================================================================================================================


@pytest.mark.parametrize(('is_admin', 'is_owner', 'expected'), (
    (True,  True,  True),
    (True,  False, True),
    (False, True,  True),
    (False, False, False),
))
def test_can_be_accepted(dummy_reservation, dummy_room, create_user, is_admin, is_owner, expected):
    user = create_user('user')
    if is_admin:
        user.rb_admin = True
    if is_owner:
        dummy_room.owner_id = user.id
    assert dummy_reservation.can_be_accepted(user) == expected


@pytest.mark.parametrize(('is_admin', 'is_created_by', 'is_booked_for', 'expected'), (
    (True,  True,  True,  True),
    (True,  True,  False, True),
    (True,  False, True,  True),
    (True,  False, False, True),
    (False, True,  True,  True),
    (False, True,  False, True),
    (False, False, True,  True),
    (False, False, False, False),
))
def test_can_be_cancelled(dummy_reservation, create_user, is_admin, is_created_by, is_booked_for, expected):
    user = create_user('user')
    user.rb_admin = is_admin
    if is_created_by:
        dummy_reservation.created_by_user = user
    if is_booked_for:
        dummy_reservation.booked_for_user = user
    assert dummy_reservation.can_be_cancelled(user) == expected


@pytest.mark.parametrize(('is_admin', 'expected'), (
    (True,  True),
    (False, False),
))
def test_can_be_deleted(dummy_reservation, dummy_user, is_admin, expected):
    if is_admin:
        dummy_user.rb_admin = True
    assert dummy_reservation.can_be_deleted(dummy_user) == expected


@pytest.mark.parametrize(('is_rejected', 'is_cancelled',
                          'is_admin', 'is_created_by', 'is_booked_for', 'is_room_owner', 'expected'), (
    # rejected/cancelled cases
    (True,  True,  True,  True,  True,  True,  False),
    (True,  True,  True,  True,  True,  False, False),
    (True,  True,  True,  True,  False, True,  False),
    (True,  True,  True,  True,  False, False, False),
    (True,  True,  True,  False, True,  True,  False),
    (True,  True,  True,  False, True,  False, False),
    (True,  True,  True,  False, False, True,  False),
    (True,  True,  True,  False, False, False, False),
    (True,  True,  False, True,  True,  True,  False),
    (True,  True,  False, True,  True,  False, False),
    (True,  True,  False, True,  False, True,  False),
    (True,  True,  False, True,  False, False, False),
    (True,  True,  False, False, True,  True,  False),
    (True,  True,  False, False, True,  False, False),
    (True,  True,  False, False, False, True,  False),
    (True,  True,  False, False, False, False, False),
    (True,  False, True,  True,  True,  True,  False),
    (True,  False, True,  True,  True,  False, False),
    (True,  False, True,  True,  False, True,  False),
    (True,  False, True,  True,  False, False, False),
    (True,  False, True,  False, True,  True,  False),
    (True,  False, True,  False, True,  False, False),
    (True,  False, True,  False, False, True,  False),
    (True,  False, True,  False, False, False, False),
    (True,  False, False, True,  True,  True,  False),
    (True,  False, False, True,  True,  False, False),
    (True,  False, False, True,  False, True,  False),
    (True,  False, False, True,  False, False, False),
    (True,  False, False, False, True,  True,  False),
    (True,  False, False, False, True,  False, False),
    (True,  False, False, False, False, True,  False),
    (True,  False, False, False, False, False, False),
    (False, True,  True,  True,  True,  True,  False),
    (False, True,  True,  True,  True,  False, False),
    (False, True,  True,  True,  False, True,  False),
    (False, True,  True,  True,  False, False, False),
    (False, True,  True,  False, True,  True,  False),
    (False, True,  True,  False, True,  False, False),
    (False, True,  True,  False, False, True,  False),
    (False, True,  True,  False, False, False, False),
    (False, True,  False, True,  True,  True,  False),
    (False, True,  False, True,  True,  False, False),
    (False, True,  False, True,  False, True,  False),
    (False, True,  False, True,  False, False, False),
    (False, True,  False, False, True,  True,  False),
    (False, True,  False, False, True,  False, False),
    (False, True,  False, False, False, True,  False),
    (False, True,  False, False, False, False, False),
    # Admin cases
    (False, False, True,  True,  True,  True,  True),
    (False, False, True,  True,  True,  False, True),
    (False, False, True,  True,  False, True,  True),
    (False, False, True,  True,  False, False, True),
    (False, False, True,  False, True,  True,  True),
    (False, False, True,  False, True,  False, True),
    (False, False, True,  False, False, True,  True),
    (False, False, True,  False, False, False, True),
    # Other cases
    (False, False, False, True,  True,  True,  True),
    (False, False, False, True,  True,  False, True),
    (False, False, False, True,  False, True,  True),
    (False, False, False, True,  False, False, True),
    (False, False, False, False, True,  True,  True),
    (False, False, False, False, True,  False, True),
    (False, False, False, False, False, True,  True),
    (False, False, False, False, False, False, False),
))
def test_can_be_modified(dummy_reservation, dummy_room, create_user,
                         is_rejected, is_cancelled, is_admin, is_created_by, is_booked_for, is_room_owner, expected):
    user = create_user('user')
    user.rb_admin = is_admin
    if is_created_by:
        dummy_reservation.created_by_user = user
    if is_booked_for:
        dummy_reservation.booked_for_user = user
    if is_room_owner:
        dummy_room.owner = user
    dummy_reservation.is_rejected = is_rejected
    dummy_reservation.is_cancelled = is_cancelled
    assert dummy_reservation.can_be_modified(user) == expected


def test_can_be_action_with_no_user(dummy_reservation):
    assert dummy_reservation.can_be_accepted(None) is False
    assert dummy_reservation.can_be_cancelled(None) is False
    assert dummy_reservation.can_be_deleted(None) is False
    assert dummy_reservation.can_be_modified(None) is False
    assert dummy_reservation.can_be_rejected(None) is False
