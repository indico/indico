# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from datetime import date

import pytest
from dateutil.relativedelta import relativedelta

from indico.core.errors import IndicoError
from indico.modules.rb import rb_settings
from indico.modules.rb.models.reservations import Reservation, RepeatFrequency, RepeatMapping
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservation_edit_logs import ReservationEditLog
from indico.testing.util import bool_matrix


pytest_plugins = 'indico.modules.rb.testing.fixtures'


@pytest.fixture
def overlapping_reservation(create_reservation):
    reservation = create_reservation(start_dt=date.today() + relativedelta(hour=2),
                                     end_dt=date.today() + relativedelta(hour=4))
    occurrence = ReservationOccurrence(start_dt=date.today() + relativedelta(hour=1),
                                       end_dt=date.today() + relativedelta(hour=5))
    return reservation, occurrence


# ======================================================================================================================
# RepeatMapping tests
# ======================================================================================================================


@pytest.mark.parametrize(('repetition', 'legacy', 'short_name', 'message'), (
    ((RepeatFrequency.NEVER, 0), None, 'none',            'Single reservation'),
    ((RepeatFrequency.DAY,   1), 0,    'daily',           'Repeat daily'),
    ((RepeatFrequency.WEEK,  1), 1,    'weekly',          'Repeat once a week'),
    ((RepeatFrequency.WEEK,  2), 2,    'everyTwoWeeks',   'Repeat once every two weeks'),
    ((RepeatFrequency.WEEK,  3), 3,    'everyThreeWeeks', 'Repeat once every three weeks'),
    ((RepeatFrequency.MONTH, 1), 4,    'monthly',         'Repeat every month'),
))
def test_repeat_mapping(repetition, legacy, short_name, message):
    assert RepeatMapping.get_message(*repetition) == message
    assert RepeatMapping.get_short_name(*repetition) == short_name
    assert RepeatMapping.convert_legacy_repeatability(legacy) == repetition


def test_repeat_mapping_invalid_legacy():
    with pytest.raises(IndicoError):
        RepeatMapping.convert_legacy_repeatability(123)


# ======================================================================================================================
# Hybrid property tests
# ======================================================================================================================


@pytest.mark.parametrize(('days_delta', 'expected'), (
    (-1, True),   # Reservation in the past
    (1,  False),  # Reservation in the future
    (0,  False),  # Reservation in course
))
def test_is_archived(create_reservation, days_delta, expected):
    start_dt = date.today() + relativedelta(days=days_delta, hour=0, minute=0)
    end_dt = date.today() + relativedelta(days=days_delta, hour=23, minute=59)
    reservation = create_reservation(start_dt=start_dt, end_dt=end_dt)
    assert reservation.is_archived == expected


@pytest.mark.parametrize(('is_accepted', 'is_rejected', 'is_cancelled', 'expected'),
                         bool_matrix('...', expect=lambda x: not any(x)))  # neither accepted/rejected/cancelled
def test_is_pending(create_reservation, is_accepted, is_rejected, is_cancelled, expected):
    reservation = create_reservation(is_accepted=is_accepted, is_rejected=is_rejected, is_cancelled=is_cancelled)
    assert reservation.is_pending == expected
    assert Reservation.find_first(is_pending=expected) == reservation


@pytest.mark.parametrize(('repeat_frequency', 'expected'), (
    (RepeatFrequency.NEVER, False),
    (RepeatFrequency.DAY,   True),
    (RepeatFrequency.WEEK,  True),
    (RepeatFrequency.MONTH, True),
))
def test_is_repeating(create_reservation, repeat_frequency, expected):
    reservation = create_reservation(repeat_frequency=repeat_frequency)
    assert reservation.is_repeating == expected


@pytest.mark.parametrize(('is_accepted', 'is_rejected', 'is_cancelled', 'expected'),
                         bool_matrix('...', expect=(True, False, False)))  # accepted, not rejected/cancelled
def test_is_valid(create_reservation, is_accepted, is_rejected, is_cancelled, expected):
    reservation = create_reservation(is_accepted=is_accepted, is_rejected=is_rejected, is_cancelled=is_cancelled)
    assert reservation.is_valid == expected
    assert Reservation.find_first(is_valid=expected) == reservation


# ======================================================================================================================
# Property tests
# ======================================================================================================================


def test_booked_for_user(dummy_reservation, dummy_user):
    assert dummy_reservation.booked_for_user == dummy_user


def test_booked_for_user_after_change(db, dummy_reservation, create_user):
    other_user = create_user(123, first_name='foo', last_name='bar')
    assert dummy_reservation.booked_for_name != other_user.full_name
    dummy_reservation.booked_for_user = other_user
    db.session.flush()
    assert dummy_reservation.booked_for_user == other_user
    assert dummy_reservation.booked_for_id == other_user.id
    assert dummy_reservation.booked_for_name == other_user.full_name


def test_created_by_user(dummy_reservation, dummy_user):
    assert dummy_reservation.created_by_user == dummy_user


def test_created_by_user_after_change(db, dummy_reservation, dummy_user):
    dummy_reservation.created_by_user = dummy_user
    db.session.flush()
    assert dummy_reservation.created_by_user == dummy_user
    assert dummy_reservation.created_by_id == dummy_user.id


def test_created_by_user_with_no_id(db, dummy_reservation):
    dummy_reservation.created_by_id = None
    db.session.flush()
    db.session.expire(dummy_reservation)
    assert dummy_reservation.created_by_user is None


def test_details_url(dummy_reservation):
    assert dummy_reservation.details_url


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
        params['start_dt'] = date.today() + relativedelta(days=-1, hour=8)
        params['end_dt'] = date.today() + relativedelta(days=-1, hour=17)
    else:
        params['start_dt'] = date.today() + relativedelta(days=1, hour=8)
        params['end_dt'] = date.today() + relativedelta(days=1, hour=17)
    reservation = create_reservation(**params)
    assert str(reservation.status_string) == expected


# ======================================================================================================================
# staticmethod tests
# ======================================================================================================================


@pytest.mark.xfail
def test_create_from_data():
    raise NotImplementedError


@pytest.mark.xfail
def test_get_with_data():
    raise NotImplementedError


def test_find_overlapping_with_different_room(overlapping_reservation, create_room):
    reservation, occurrence = overlapping_reservation
    assert reservation in Reservation.find_overlapping_with(room=reservation.room, occurrences=[occurrence]).all()
    assert reservation not in Reservation.find_overlapping_with(room=create_room(), occurrences=[occurrence]).all()


def test_find_overlapping_with_is_not_valid(overlapping_reservation, dummy_user):
    reservation, occurrence = overlapping_reservation
    assert reservation in Reservation.find_overlapping_with(room=reservation.room,
                                                            occurrences=[occurrence]).all()
    reservation.cancel(dummy_user, silent=True)
    assert reservation not in Reservation.find_overlapping_with(room=reservation.room,
                                                                occurrences=[occurrence]).all()


def test_find_overlapping_with_skip_reservation(overlapping_reservation):
    reservation, occurrence = overlapping_reservation
    assert reservation in Reservation.find_overlapping_with(room=reservation.room, occurrences=[occurrence]).all()
    assert reservation not in Reservation.find_overlapping_with(room=reservation.room,
                                                                occurrences=[occurrence],
                                                                skip_reservation_id=reservation.id).all()


# ======================================================================================================================
# method tests
# ======================================================================================================================


@pytest.mark.xfail
def test_accept():
    raise NotImplementedError


@pytest.mark.parametrize('silent', (True, False))
def test_cancel(smtp, create_reservation, dummy_user, silent):
    reservation = create_reservation(start_dt=date.today() + relativedelta(hour=8),
                                     end_dt=date.today() + relativedelta(days=10, hour=17),
                                     repeat_frequency=RepeatFrequency.DAY)
    assert not reservation.is_cancelled
    assert not any(occ.is_cancelled for occ in reservation.occurrences)
    reservation.cancel(user=dummy_user, reason='cancelled', silent=silent)
    assert reservation.is_cancelled
    assert reservation.rejection_reason == 'cancelled'
    assert all(occ.is_cancelled for occ in reservation.occurrences)
    if silent:
        assert not reservation.edit_logs.count()
        assert not smtp.outbox
    else:
        assert reservation.edit_logs.count() == 1
        assert smtp.outbox


@pytest.mark.parametrize('silent', (True, False))
def test_reject(smtp, create_reservation, dummy_user, silent):
    reservation = create_reservation(start_dt=date.today() + relativedelta(hour=8),
                                     end_dt=date.today() + relativedelta(days=10, hour=17),
                                     repeat_frequency=RepeatFrequency.DAY)
    assert not reservation.is_rejected
    assert not any(occ.is_rejected for occ in reservation.occurrences)
    reservation.reject(user=dummy_user, reason='rejected', silent=silent)
    assert reservation.is_rejected
    assert reservation.rejection_reason == 'rejected'
    assert all(occ.is_rejected for occ in reservation.occurrences)
    if silent:
        assert not reservation.edit_logs.count()
        assert not smtp.outbox
    else:
        assert reservation.edit_logs.count() == 1
        assert smtp.outbox


def test_add_edit_log(db, dummy_reservation):
    dummy_reservation.add_edit_log(ReservationEditLog(user_name='user', info='Some change'))
    assert dummy_reservation.edit_logs.count() == 1


@pytest.mark.parametrize(('is_admin', 'is_owner', 'expected'), bool_matrix('..', expect=any))
def test_can_be_accepted_rejected(dummy_reservation, create_user, is_admin, is_owner, expected):
    user = create_user(123, rb_admin=is_admin)
    if is_owner:
        dummy_reservation.room.owner = user
    assert dummy_reservation.can_be_accepted(user) == expected
    assert dummy_reservation.can_be_rejected(user) == expected


@pytest.mark.parametrize(('is_admin', 'is_created_by', 'is_booked_for', 'expected'),
                         bool_matrix('...', expect=any))  # admin/creator/booked-for, one is enough
def test_can_be_cancelled(dummy_reservation, create_user, is_admin, is_created_by, is_booked_for, expected):
    user = create_user(123, rb_admin=is_admin)
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
        rb_settings.acls.add_principal('admin_principals', dummy_user)
    assert dummy_reservation.can_be_deleted(dummy_user) == expected


@pytest.mark.parametrize(
    ('is_rejected', 'is_cancelled', 'is_admin', 'is_created_by', 'is_booked_for', 'is_room_owner', 'expected'),
    bool_matrix('!00....', expect=False) +                # rejected or cancelled
    bool_matrix(' 001...', expect=True) +                 # admin
    bool_matrix(' 000...', expect=lambda x: any(x[3:]))   # creator, booked for, room owner
)
def test_can_be_modified(dummy_reservation, create_user,
                         is_rejected, is_cancelled, is_admin, is_created_by, is_booked_for, is_room_owner, expected):
    user = create_user(123, rb_admin=is_admin)
    if is_created_by:
        dummy_reservation.created_by_user = user
    if is_booked_for:
        dummy_reservation.booked_for_user = user
    if is_room_owner:
        dummy_reservation.room.owner = user
    dummy_reservation.is_rejected = is_rejected
    dummy_reservation.is_cancelled = is_cancelled
    assert dummy_reservation.can_be_modified(user) == expected


@pytest.mark.parametrize(
    ('is_admin', 'is_room_owner', 'expected'),
    bool_matrix('..', expect=any)
)
def test_can_be_rejected(dummy_reservation, create_user, is_admin, is_room_owner, expected):
    user = create_user(123, rb_admin=is_admin)
    if is_room_owner:
        dummy_reservation.room.owner = user
    assert dummy_reservation.can_be_rejected(user) == expected


def test_can_be_action_with_no_user(dummy_reservation):
    assert not dummy_reservation.can_be_accepted(None)
    assert not dummy_reservation.can_be_cancelled(None)
    assert not dummy_reservation.can_be_deleted(None)
    assert not dummy_reservation.can_be_modified(None)
    assert not dummy_reservation.can_be_rejected(None)


@pytest.mark.xfail
def test_create_occurrences():
    raise NotImplementedError


def test_find_excluded_days(db, create_reservation):
    reservation = create_reservation(start_dt=date.today() + relativedelta(hour=8),
                                     end_dt=date.today() + relativedelta(days=5, hour=10),
                                     repeat_frequency=RepeatFrequency.DAY)
    for occ in reservation.occurrences[::2]:
        occ.is_cancelled = True
    db.session.flush()
    assert set(reservation.find_excluded_days().all()) == {occ for occ in reservation.occurrences if not occ.is_valid}


def test_find_overlapping(create_reservation):
    resv1 = create_reservation(is_accepted=False)
    assert not resv1.find_overlapping().count()
    resv2 = create_reservation(is_accepted=False)
    assert resv1.find_overlapping().one() == resv2


def test_locator(dummy_reservation, dummy_location):
    assert dummy_reservation.locator == {'roomLocation': dummy_location.name, 'resvID': dummy_reservation.id}


@pytest.mark.xfail
def test_get_conflicting_occurrences():
    raise NotImplementedError


def test_get_vc_equipment(db, dummy_reservation, create_equipment_type):
    foo = create_equipment_type(u'foo')
    vc = create_equipment_type(u'Video conference')
    vc_items = [create_equipment_type(u'vc1'), create_equipment_type(u'vc2')]
    vc.children += vc_items
    dummy_reservation.room.available_equipment.extend(vc_items + [vc, foo])
    dummy_reservation.used_equipment = [vc_items[0]]
    db.session.flush()
    assert set(dummy_reservation.get_vc_equipment().all()) == {vc_items[0]}


@pytest.mark.parametrize(('is_booked_for', 'expected'), (
    (True, True),
    (False, False),
))
def test_is_booked_for(dummy_reservation, dummy_user, create_user, is_booked_for, expected):
    if not is_booked_for:
        dummy_reservation.booked_for_user = create_user(123)
    assert dummy_reservation.is_booked_for(dummy_user) == expected


def test_is_booked_for_no_user(dummy_reservation):
    assert not dummy_reservation.is_booked_for(None)


def test_is_created_by(dummy_reservation, dummy_user):
    assert dummy_reservation.is_owned_by(dummy_user)


@pytest.mark.xfail
def test_modify():
    raise NotImplementedError
