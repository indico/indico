# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import date, datetime, time
from itertools import izip

import pytest
from dateutil.relativedelta import relativedelta

from indico.core.errors import IndicoError
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence, ReservationOccurrenceState
from indico.modules.rb.models.reservations import RepeatFrequency
from indico.testing.util import extract_emails


pytest_plugins = 'indico.modules.rb.testing.fixtures'


@pytest.fixture
def creation_params():
    return {'start': date.today() + relativedelta(hour=8),
            'end': date.today() + relativedelta(days=1, hour=17),
            'repetition': (RepeatFrequency.DAY, 1)}


@pytest.fixture(params=(
    (0, 1, (None, None)),  # Before
    (1, 2, (None, None)),  # Right before
    (1, 3, (2, 3)),        # Overlapping start
    (1, 5, (2, 4)),        # Overlapping start and end
    (2, 4, (2, 4)),        # Exactly the same
    (3, 5, (3, 4)),        # Overlapping end
    (4, 5, (None, None)),  # Right after
    (5, 6, (None, None)),  # After
))
def overlapping_combination_from_2am_to_4am(request):
    def _get_values(boolean=True):
        start_hour = request.param[0]
        end_hour = request.param[1]
        expected_overlap = any(request.param[2]) if boolean else request.param[2]
        return start_hour, end_hour, expected_overlap
    return _get_values


@pytest.fixture
def overlapping_occurrences(create_occurrence):
    db_occ = create_occurrence(start_dt=date.today() + relativedelta(hour=2),
                               end_dt=date.today() + relativedelta(hour=4))
    occ = ReservationOccurrence(start_dt=date.today() + relativedelta(hour=1),
                                end_dt=date.today() + relativedelta(hour=5))
    return db_occ, occ


# ======================================================================================================================
# Hybrid property tests
# ======================================================================================================================


def test_date(dummy_occurrence):
    assert dummy_occurrence.date == date.today()
    assert ReservationOccurrence.find_first(date=date.today()) == dummy_occurrence


# ======================================================================================================================
# staticmethod tests
# ======================================================================================================================


def test_create_series_for_reservation(dummy_reservation):
    occurrences = ReservationOccurrence.iter_create_occurrences(start=dummy_reservation.start_dt,
                                                                end=dummy_reservation.end_dt,
                                                                repetition=dummy_reservation.repetition)
    for occ1, occ2 in izip(dummy_reservation.occurrences, occurrences):
        assert occ1.start_dt == occ2.start_dt
        assert occ1.end_dt == occ2.end_dt
        assert occ1.is_cancelled == dummy_reservation.is_cancelled
        assert occ1.is_rejected == dummy_reservation.is_rejected
        assert occ1.rejection_reason == dummy_reservation.rejection_reason


def test_create_series(creation_params):
    for occ1, occ2 in izip(list(ReservationOccurrence.iter_create_occurrences(**creation_params)),
                           ReservationOccurrence.create_series(**creation_params)):
        assert occ1.start_dt == occ2.start_dt
        assert occ1.end_dt == occ2.end_dt


def test_iter_create_occurrences(creation_params):
    occurrences = list(ReservationOccurrence.iter_create_occurrences(**creation_params))
    assert len(occurrences) == 2
    for occ in occurrences:
        assert occ.start_dt.time() == time(8)
        assert occ.end_dt.time() == time(17)


def test_iter_start_time_invalid():
    invalid_frequency = -1
    assert invalid_frequency not in RepeatFrequency
    with pytest.raises(IndicoError):
        ReservationOccurrence.iter_start_time(start=date.today(), end=date.today(), repetition=(invalid_frequency, 0))


@pytest.mark.parametrize('interval', (0, 1, 2))
def test_iter_start_time_single(interval):
    days = list(ReservationOccurrence.iter_start_time(start=date.today() + relativedelta(hour=8),
                                                      end=date.today() + relativedelta(hour=17),
                                                      repetition=(RepeatFrequency.NEVER, interval)))
    assert len(days) == 1


@pytest.mark.parametrize(('interval', 'days_elapsed', 'expected_length'), (
    (0, 0,  None),
    (1, 0,  1),
    (1, 10, 11),
    (2, 0,  None),
))
def test_iter_start_time_daily(interval, days_elapsed, expected_length):
    assert days_elapsed >= 0
    params = {'start': date.today() + relativedelta(hour=8),
              'end': date.today() + relativedelta(days=days_elapsed, hour=17),
              'repetition': (RepeatFrequency.DAY, interval)}
    if expected_length is None:
        with pytest.raises(IndicoError):
            ReservationOccurrence.iter_start_time(**params)
    else:
        days = list(ReservationOccurrence.iter_start_time(**params))
        assert len(days) == expected_length
        for i, day in enumerate(days):
            assert day.date() == date.today() + relativedelta(days=i)


@pytest.mark.parametrize(('interval', 'days_elapsed', 'expected_length'), (
    (0, 0,  None),
    (1, 0,  1),
    (1, 7,  2),
    (1, 21, 4),
    (2, 7,  1),
    (2, 14, 2),
    (2, 42, 4),
    (3, 14, 1),
    (3, 21, 2),
    (3, 63, 4),
    (4, 0,  1),
    (4, 27, 1),
    (4, 28, 2),
    (4, 83, 3),
    (4, 84, 4),
))
def test_iter_start_time_weekly(interval, days_elapsed, expected_length):
    assert days_elapsed >= 0
    params = {'start': date.today() + relativedelta(hour=8),
              'end': date.today() + relativedelta(days=days_elapsed, hour=17),
              'repetition': (RepeatFrequency.WEEK, interval)}
    if expected_length is None:
        with pytest.raises(IndicoError):
            ReservationOccurrence.iter_start_time(**params)
    else:
        days = list(ReservationOccurrence.iter_start_time(**params))
        assert len(days) == expected_length
        for i, day in enumerate(days):
            assert day.date() == date.today() + relativedelta(weeks=i * interval)


@pytest.mark.parametrize(('interval', 'days_elapsed', 'expected_length'), (
    (0, 0,  None),
    (1, 0,  1),
    (1, 40, 2)
))
def test_iter_start_time_monthly(interval, days_elapsed, expected_length):
    assert days_elapsed >= 0
    params = {'start': date.today() + relativedelta(hour=8),
              'end': date.today() + relativedelta(days=days_elapsed, hour=17),
              'repetition': (RepeatFrequency.MONTH, interval)}
    if expected_length is None:
        with pytest.raises(IndicoError):
            ReservationOccurrence.iter_start_time(**params)
    else:
        days = list(ReservationOccurrence.iter_start_time(**params))
        weekday = params['start'].weekday()
        assert len(days) == expected_length
        assert all(day.weekday() == weekday for day in days)


def test_iter_start_time_monthly_5th_monday_is_always_last():
    start_dt = date(2014, 9, 29) + relativedelta(hour=8)  # 5th monday of september
    end_dt = start_dt + relativedelta(days=100, hour=17)
    params = {'start': start_dt, 'end': end_dt, 'repetition': (RepeatFrequency.MONTH, 1)}

    days = list(ReservationOccurrence.iter_start_time(**params))
    assert len(days) == 4
    assert days[1].date() == date(2014, 10, 27)  # 4th monday of october
    assert days[2].date() == date(2014, 11, 24)  # 4th monday of october
    assert days[3].date() == date(2014, 12, 29)  # 5th monday of october


def test_filter_overlap(create_occurrence, overlapping_combination_from_2am_to_4am):
    start_hour, end_hour, expected = overlapping_combination_from_2am_to_4am()
    occ1 = create_occurrence(start_dt=date.today() + relativedelta(hour=2),
                             end_dt=date.today() + relativedelta(hour=4))
    occ2 = ReservationOccurrence(start_dt=date.today() + relativedelta(hour=start_hour),
                                 end_dt=date.today() + relativedelta(hour=end_hour))
    overlap_filter = ReservationOccurrence.filter_overlap([occ2])
    assert (occ1 in ReservationOccurrence.find_all(overlap_filter)) == expected


def test_find_overlapping_with_different_room(overlapping_occurrences, create_room):
    db_occ, occ = overlapping_occurrences
    assert db_occ in ReservationOccurrence.find_overlapping_with(room=db_occ.reservation.room, occurrences=[occ]).all()
    assert db_occ not in ReservationOccurrence.find_overlapping_with(room=create_room(), occurrences=[occ]).all()


def test_find_overlapping_with_is_not_valid(db, overlapping_occurrences):
    db_occ, occ = overlapping_occurrences
    assert db_occ in ReservationOccurrence.find_overlapping_with(room=db_occ.reservation.room,
                                                                 occurrences=[occ]).all()
    db_occ.state = ReservationOccurrenceState.cancelled
    db.session.flush()
    assert db_occ not in ReservationOccurrence.find_overlapping_with(room=db_occ.reservation.room,
                                                                     occurrences=[occ]).all()


def test_find_overlapping_with_skip_reservation(overlapping_occurrences):
    db_occ, occ = overlapping_occurrences
    assert db_occ in ReservationOccurrence.find_overlapping_with(room=db_occ.reservation.room, occurrences=[occ]).all()
    assert db_occ not in ReservationOccurrence.find_overlapping_with(room=db_occ.reservation.room,
                                                                     occurrences=[occ],
                                                                     skip_reservation_id=db_occ.reservation.id).all()


# ======================================================================================================================
# method tests
# ======================================================================================================================


@pytest.mark.parametrize(('silent', 'reason'), (
    (True,  'cancelled'),
    (True,  None),
    (False, 'cancelled'),
    (False, None),
))
def test_cancel(smtp, create_reservation, dummy_user, silent, reason):
    reservation = create_reservation(start_dt=date.today() + relativedelta(hour=8),
                                     end_dt=date.today() + relativedelta(days=1, hour=17),
                                     repeat_frequency=RepeatFrequency.DAY)
    assert reservation.occurrences.count() > 1
    occurrence = reservation.occurrences[0]
    occurrence.cancel(user=dummy_user, reason=reason, silent=silent)
    assert occurrence.is_cancelled
    assert occurrence.rejection_reason == reason
    assert not occurrence.reservation.is_cancelled
    if silent:
        assert not occurrence.reservation.edit_logs.count()
        assert not smtp.outbox
    else:
        assert occurrence.reservation.edit_logs.count() == 1
        assert occurrence.reservation.edit_logs[0].user_name == dummy_user.full_name
        extract_emails(smtp, count=2, regex=True, subject=r'Booking cancelled .+ \(SINGLE OCCURRENCE\)')
        if reason:
            assert len(occurrence.reservation.edit_logs[0].info) == 2
        else:
            assert len(occurrence.reservation.edit_logs[0].info) == 1
    assert not smtp.outbox


@pytest.mark.parametrize('silent', (True, False))
def test_cancel_single_occurrence(smtp, create_occurrence, dummy_user, silent, freeze_time):
    occ = create_occurrence(start_dt=datetime.combine(date.today(), time(11)),
                            end_dt=datetime.combine(date.today(), time(12)))
    freeze_time(datetime.combine(date.today(), time(11, 10)))
    occ.cancel(user=dummy_user, reason='cancelled', silent=silent)
    assert occ.is_cancelled
    assert occ.rejection_reason == 'cancelled'
    assert occ.reservation.is_cancelled
    assert occ.reservation.rejection_reason == 'cancelled'
    if silent:
        assert not occ.reservation.edit_logs.count()
    else:
        assert occ.reservation.edit_logs.count()
        mails = extract_emails(smtp, count=2, regex=True, subject=r'Booking cancelled')
        assert not any('SINGLE OCCURRENCE' in mail['subject'] for mail in mails)
    assert not smtp.outbox


@pytest.mark.parametrize('silent', (True, False))
def test_reject(smtp, create_reservation, dummy_user, silent):
    reservation = create_reservation(start_dt=date.today() + relativedelta(hour=8),
                                     end_dt=date.today() + relativedelta(days=1, hour=17),
                                     repeat_frequency=RepeatFrequency.DAY)
    assert reservation.occurrences.count() > 1
    occurrence = reservation.occurrences[0]
    occurrence.reject(user=dummy_user, reason='cancelled', silent=silent)
    assert occurrence.is_rejected
    assert occurrence.rejection_reason == 'cancelled'
    assert not occurrence.reservation.is_rejected
    if silent:
        assert not occurrence.reservation.edit_logs.count()
        assert not smtp.outbox
    else:
        assert occurrence.reservation.edit_logs.count() == 1
        assert occurrence.reservation.edit_logs[0].user_name == dummy_user.full_name
        assert len(occurrence.reservation.edit_logs[0].info) == 2
        extract_emails(smtp, count=2, regex=True, subject=r'Booking rejected on .+ \(SINGLE OCCURRENCE\)')
    assert not smtp.outbox


@pytest.mark.parametrize('silent', (True, False))
def test_reject_single_occurrence(smtp, dummy_occurrence, dummy_user, silent):
    dummy_occurrence.reject(user=dummy_user, reason='rejected', silent=silent)
    assert dummy_occurrence.is_rejected
    assert dummy_occurrence.rejection_reason == 'rejected'
    assert dummy_occurrence.reservation.is_rejected
    assert dummy_occurrence.reservation.rejection_reason == 'rejected'
    if silent:
        assert not dummy_occurrence.reservation.edit_logs.count()
    else:
        assert dummy_occurrence.reservation.edit_logs.count()
        mails = extract_emails(smtp, count=2, regex=True, subject='Booking rejected')
        assert not any('SINGLE OCCURRENCE' in mail['subject'] for mail in mails)
    assert not smtp.outbox


def test_get_overlap(overlapping_combination_from_2am_to_4am):
    start_hour, end_hour, expected_overlap = overlapping_combination_from_2am_to_4am(boolean=False)
    occ1 = ReservationOccurrence(start_dt=date.today() + relativedelta(hour=2),
                                 end_dt=date.today() + relativedelta(hour=4))
    occ2 = ReservationOccurrence(start_dt=date.today() + relativedelta(hour=start_hour),
                                 end_dt=date.today() + relativedelta(hour=end_hour))
    if expected_overlap != (None, None):
        overlap_start = date.today() + relativedelta(hour=expected_overlap[0])
        overlap_end = date.today() + relativedelta(hour=expected_overlap[1])
        assert occ1.get_overlap(occ2) == (overlap_start, overlap_end)
    else:
        assert occ1.get_overlap(occ2) == expected_overlap


def test_get_overlap_different_rooms(create_occurrence, create_room):
    other_room = create_room()
    occ1 = create_occurrence()
    occ2 = create_occurrence(room=other_room)
    with pytest.raises(ValueError):
        occ1.get_overlap(occ2)


@pytest.mark.parametrize('skip_self', (True, False))
def test_get_overlaps_self(dummy_occurrence, skip_self):
    if skip_self:
        expected_overlap = (None, None)
    else:
        expected_overlap = (dummy_occurrence.start_dt, dummy_occurrence.end_dt)
    assert dummy_occurrence.get_overlap(dummy_occurrence, skip_self=skip_self) == expected_overlap


def test_overlaps(overlapping_combination_from_2am_to_4am):
    start_hour, end_hour, expected = overlapping_combination_from_2am_to_4am()
    occ1 = ReservationOccurrence(start_dt=date.today() + relativedelta(hour=2),
                                 end_dt=date.today() + relativedelta(hour=4))
    occ2 = ReservationOccurrence(start_dt=date.today() + relativedelta(hour=start_hour),
                                 end_dt=date.today() + relativedelta(hour=end_hour))
    assert occ1.overlaps(occ2) == expected


def test_overlaps_different_rooms(create_occurrence, create_room):
    other_room = create_room()
    occ1 = create_occurrence()
    occ2 = create_occurrence(room=other_room)
    with pytest.raises(ValueError):
        occ1.overlaps(occ2)


@pytest.mark.parametrize('skip_self', (True, False))
def test_overlaps_self(dummy_occurrence, skip_self):
    assert dummy_occurrence.overlaps(dummy_occurrence, skip_self=skip_self) == (not skip_self)


@pytest.mark.parametrize('state', ReservationOccurrenceState)
def test_can_reject(create_reservation, dummy_user, state):
    reservation = create_reservation(start_dt=date.today() - relativedelta(days=1, hour=8),
                                     end_dt=date.today() + relativedelta(days=1, hour=17),
                                     repeat_frequency=RepeatFrequency.DAY)
    reservation.room.update_principal(dummy_user, full_access=True)
    occ = reservation.occurrences[0]
    occ.state = state
    assert occ.can_reject(dummy_user) == occ.is_valid


def test_can_cancel(create_reservation, dummy_user, freeze_time):
    reservation = create_reservation(start_dt=date.today() - relativedelta(days=1, hour=8),
                                     end_dt=date.today() + relativedelta(days=1, hour=17),
                                     repeat_frequency=RepeatFrequency.DAY)
    freeze_time(datetime.combine(date.today(), time(18, 0)))
    assert not reservation.occurrences[0].can_cancel(dummy_user)
    assert not reservation.occurrences[1].can_cancel(dummy_user)
    assert reservation.occurrences[-1].can_cancel(dummy_user)


def test_cannot_cancel_archived_reservation(create_reservation, dummy_user, freeze_time):
    reservation = create_reservation(start_dt=datetime.combine(date.today(), time(11)),
                                     end_dt=datetime.combine(date.today(), time(17)),
                                     repeat_frequency=RepeatFrequency.NEVER)
    freeze_time(datetime.combine(date.today(), time(8)))
    assert reservation.can_cancel(dummy_user)

    freeze_time(datetime.combine(date.today(), time(13)))
    assert reservation.can_cancel(dummy_user)

    freeze_time(datetime.combine(date.today(), time(17)))
    assert reservation.can_cancel(dummy_user)

    freeze_time(datetime.combine(date.today(), time(17, 1)))
    assert not reservation.can_cancel(dummy_user)
