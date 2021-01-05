# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import date, datetime, time

import pytest
from dateutil.relativedelta import relativedelta

from indico.modules.rb.models.reservation_edit_logs import ReservationEditLog
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence, ReservationOccurrenceState
from indico.modules.rb.models.reservations import RepeatFrequency, RepeatMapping, Reservation, ReservationState


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


@pytest.mark.parametrize(('repetition', 'message'), (
    ((RepeatFrequency.NEVER, 0), 'single booking'),
    ((RepeatFrequency.DAY,   1), 'daily booking'),
    ((RepeatFrequency.WEEK,  1), 'weekly'),
    ((RepeatFrequency.WEEK,  2), 'every 2 weeks'),
    ((RepeatFrequency.MONTH, 1), 'monthly'),
    ((RepeatFrequency.MONTH, 2), 'every 2 months'),
))
def test_repeat_mapping(repetition, message):
    assert RepeatMapping.get_message(*repetition) == message


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


@pytest.mark.parametrize(('repeat_frequency', 'expected'), (
    (RepeatFrequency.NEVER, False),
    (RepeatFrequency.DAY,   True),
    (RepeatFrequency.WEEK,  True),
    (RepeatFrequency.MONTH, True),
))
def test_is_repeating(create_reservation, repeat_frequency, expected):
    reservation = create_reservation(repeat_frequency=repeat_frequency)
    assert reservation.is_repeating == expected


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


def test_external_details_url(dummy_reservation):
    assert dummy_reservation.external_details_url


def test_location_name(dummy_reservation, dummy_location):
    assert dummy_location.name == dummy_reservation.location_name


def test_repetition(dummy_reservation):
    assert (dummy_reservation.repeat_frequency, dummy_reservation.repeat_interval) == dummy_reservation.repetition


# ======================================================================================================================
# staticmethod tests
# ======================================================================================================================


def test_find_overlapping_with_different_room(overlapping_reservation, create_room):
    reservation, occurrence = overlapping_reservation
    assert reservation in Reservation.find_overlapping_with(room=reservation.room, occurrences=[occurrence]).all()
    assert reservation not in Reservation.find_overlapping_with(room=create_room(), occurrences=[occurrence]).all()


def test_find_overlapping_with_is_not_valid(overlapping_reservation, dummy_user, freeze_time):
    freeze_time(datetime.combine(date.today(), time(1)))
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


@pytest.mark.parametrize('silent', (True, False))
def test_cancel(smtp, create_reservation, dummy_user, silent, freeze_time):
    reservation = create_reservation(start_dt=date.today() + relativedelta(hour=8),
                                     end_dt=date.today() + relativedelta(days=10, hour=17),
                                     repeat_frequency=RepeatFrequency.DAY)
    freeze_time(datetime.combine(date.today(), time(7, 30)))
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


@pytest.mark.parametrize('reason', ('My reason.', None))
def test_accept(smtp, create_reservation, dummy_user, reason):
    reservation = create_reservation(start_dt=date.today() + relativedelta(hour=8),
                                     end_dt=date.today() + relativedelta(days=10, hour=17),
                                     repeat_frequency=RepeatFrequency.DAY)
    assert not reservation.is_rejected
    assert not any(occ.is_rejected for occ in reservation.occurrences)
    reservation.accept(user=dummy_user, reason=reason)
    assert reservation.is_accepted
    assert len(smtp.outbox) == 2

    if reason:
        assert ['My reason' in mail.as_string() for mail in smtp.outbox]
        assert reservation.edit_logs.one().info == ['Reservation accepted: My reason.']
    else:
        assert ['My reason' not in mail.as_string() for mail in smtp.outbox]
        assert reservation.edit_logs.one().info == ['Reservation accepted']


def test_add_edit_log(dummy_reservation):
    dummy_reservation.add_edit_log(ReservationEditLog(user_name='user', info='Some change'))
    assert dummy_reservation.edit_logs.count() == 1


@pytest.mark.parametrize('can_moderate', (True, False))
@pytest.mark.parametrize('is_pending', (True, False))
def test_moderation(dummy_reservation, create_user, is_pending, can_moderate):
    user = create_user(123)
    if is_pending:
        dummy_reservation.state = ReservationState.pending
    if can_moderate:
        dummy_reservation.room.update_principal(user, permissions={'moderate'})
    assert dummy_reservation.can_accept(user) == (is_pending and can_moderate)
    assert dummy_reservation.can_reject(user) == can_moderate


@pytest.mark.parametrize('is_manager', (True, False))
@pytest.mark.parametrize('is_past', (True, False))
@pytest.mark.parametrize('state', ReservationState)
@pytest.mark.parametrize('is_admin', (True, False))
def test_room_manager_actions(create_reservation, create_user, is_manager, is_past, state, is_admin):
    user = create_user(123, rb_admin=is_admin)
    day_offset = -1 if is_past else 1
    reservation = create_reservation(start_dt=date.today() + relativedelta(days=day_offset, hour=8, minute=30),
                                     end_dt=date.today() + relativedelta(days=day_offset, hour=8, minute=30))
    reservation.state = state
    if is_manager:
        reservation.room.update_principal(user, full_access=True)
    invalid_state = state in (ReservationState.cancelled, ReservationState.rejected)
    assert reservation.can_accept(user) == (reservation.is_pending and (is_manager or is_admin) and not invalid_state)
    assert reservation.can_reject(user) == (not invalid_state and (is_manager or is_admin))
    assert reservation.can_cancel(user) == (not is_past and not invalid_state and is_admin)
    assert reservation.can_edit(user) == (((is_manager and not is_past) or is_admin) and not invalid_state)
    assert reservation.can_delete(user) == (is_admin and invalid_state)


@pytest.mark.parametrize('is_creator', (True, False))
@pytest.mark.parametrize('is_bookee', (True, False))
@pytest.mark.parametrize('is_past', (True, False))
@pytest.mark.parametrize('state', ReservationState)
def test_user_actions(create_user, create_reservation, is_creator, is_bookee, is_past, state):
    user = create_user(123)
    day_offset = -1 if is_past else 1
    reservation = create_reservation(start_dt=date.today() + relativedelta(days=day_offset, hour=8, minute=30),
                                     end_dt=date.today() + relativedelta(days=day_offset, hour=8, minute=30),
                                     state=state)
    if is_creator:
        reservation.created_by_user = user
    if is_bookee:
        reservation.booked_for_user = user
    valid_state = state in (ReservationState.pending, ReservationState.accepted)
    assert reservation.can_cancel(user) == ((is_creator or is_bookee) and not is_past and valid_state)
    assert reservation.can_edit(user) == ((is_creator or is_bookee) and not is_past and valid_state)


def test_actions_no_user(dummy_reservation):
    assert not dummy_reservation.can_accept(None)
    assert not dummy_reservation.can_cancel(None)
    assert not dummy_reservation.can_delete(None)
    assert not dummy_reservation.can_edit(None)
    assert not dummy_reservation.can_reject(None)


def test_find_excluded_days(db, create_reservation):
    reservation = create_reservation(start_dt=date.today() + relativedelta(hour=8),
                                     end_dt=date.today() + relativedelta(days=5, hour=10),
                                     repeat_frequency=RepeatFrequency.DAY)
    for occ in reservation.occurrences[::2]:
        occ.state = ReservationOccurrenceState.cancelled
    db.session.flush()
    assert set(reservation.find_excluded_days().all()) == {occ for occ in reservation.occurrences if not occ.is_valid}


def test_find_overlapping(create_reservation):
    resv1 = create_reservation(state=ReservationState.pending)
    assert not resv1.find_overlapping().count()
    resv2 = create_reservation(state=ReservationState.pending)
    assert resv1.find_overlapping().one() == resv2


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
