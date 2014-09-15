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

from datetime import date

import pytest
from dateutil.relativedelta import relativedelta

from indico.core.errors import IndicoError
from indico.modules.rb.models.reservations import RepeatFrequency
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.testing.util import bool_matrix


pytest_plugins = 'indico.modules.rb.testing.fixtures'


# ======================================================================================================================
# Hybrid property tests
# ======================================================================================================================


def test_date(dummy_occurrence):
    assert dummy_occurrence.date == date.today()
    assert ReservationOccurrence.find_first(date=date.today()) == dummy_occurrence


@pytest.mark.parametrize(('is_rejected', 'is_cancelled', 'expected'),
                         bool_matrix('..', expect=lambda x: not any(x)))
def test_is_valid(db, dummy_occurrence, is_rejected, is_cancelled, expected):
    dummy_occurrence.is_rejected = is_rejected
    dummy_occurrence.is_cancelled = is_cancelled
    db.session.flush()
    assert dummy_occurrence.is_valid == expected
    assert ReservationOccurrence.find_first(is_valid=expected) == dummy_occurrence


# ======================================================================================================================
# staticmethod tests
# ======================================================================================================================


@pytest.mark.parametrize('interval', (
    (0),
    (1),
    (2),
))
def test_iter_start_time_single(interval):
    days = list(ReservationOccurrence.iter_start_time(start=date.today() + relativedelta(hour=8),
                                                      end=date.today() + relativedelta(hour=17),
                                                      repetition=(RepeatFrequency.NEVER, interval)))
    assert len(days) == 1


@pytest.mark.parametrize(('interval', 'days_elapsed', 'expected_length'), (
    (0, 0, 1),
    (2, 0, 1),
    (0, 10, 11),
    (2, 10, 11),
))
def test_iter_start_time_daily(interval, days_elapsed, expected_length):
    assert days_elapsed >= 0
    params = {'start': date.today() + relativedelta(hour=8),
              'end': date.today() + relativedelta(days=days_elapsed, hour=17),
              'repetition': (RepeatFrequency.DAY, interval)}
    days = list(ReservationOccurrence.iter_start_time(**params))
    assert len(days) == expected_length
    for i, day in enumerate(days):
        assert day.date() == date.today() + relativedelta(days=i)


@pytest.mark.parametrize(('interval', 'days_elapsed', 'expected_length'), (
    (0, 0, None),
    (1, 0, 1),
    (1, 7, 2),
    (1, 21, 4),
    (2, 7, 1),
    (2, 14, 2),
    (2, 42, 4),
    (3, 14, 1),
    (3, 21, 2),
    (3, 63, 4),
    (4, 0, None),
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
    (0, 0, None),
    (1, 0, 1),
    (1, 40, 2),
    (2, 0, None),
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


def test_iter_start_time_invalid():
    invalid_frequency = -1
    assert invalid_frequency not in RepeatFrequency
    with pytest.raises(IndicoError):
        ReservationOccurrence.iter_start_time(start=date.today(), end=date.today(), repetition=(invalid_frequency, 0))


# ======================================================================================================================
# method tests
# ======================================================================================================================


def test_cancel(create_reservation, dummy_user):
    reservation = create_reservation(start_dt=date.today() + relativedelta(hour=8),
                                     end_dt=date.today() + relativedelta(days=1, hour=17),
                                     repeat_frequency=RepeatFrequency.DAY)
    assert reservation.occurrences.count() > 1
    occurrence = reservation.occurrences[0]
    occurrence.cancel(user=dummy_user, reason='cancelled', silent=True)
    assert occurrence.is_cancelled
    assert occurrence.rejection_reason == 'cancelled'
    assert not occurrence.reservation.is_cancelled


def test_cancel_single_occurrence(dummy_occurrence, dummy_user):
    dummy_occurrence.cancel(user=dummy_user, reason='cancelled', silent=True)
    assert dummy_occurrence.is_cancelled
    assert dummy_occurrence.rejection_reason == 'cancelled'
    assert dummy_occurrence.reservation.is_cancelled
    assert dummy_occurrence.reservation.rejection_reason == 'cancelled'


def test_reject(create_reservation, dummy_user):
    reservation = create_reservation(start_dt=date.today() + relativedelta(hour=8),
                                     end_dt=date.today() + relativedelta(days=1, hour=17),
                                     repeat_frequency=RepeatFrequency.DAY)
    assert reservation.occurrences.count() > 1
    occurrence = reservation.occurrences[0]
    occurrence.reject(user=dummy_user, reason='cancelled', silent=True)
    assert occurrence.is_rejected
    assert occurrence.rejection_reason == 'cancelled'
    assert not occurrence.reservation.is_rejected


def test_reject_single_occurrence(dummy_occurrence, dummy_user):
    dummy_occurrence.reject(user=dummy_user, reason='rejected', silent=True)
    assert dummy_occurrence.is_rejected
    assert dummy_occurrence.rejection_reason == 'rejected'
    assert dummy_occurrence.reservation.is_rejected
    assert dummy_occurrence.reservation.rejection_reason == 'rejected'


@pytest.mark.parametrize(('start_hour', 'end_hour', 'expected_overlap'), (
    # Before
    (0, 1, (None, None)),
    # Right before
    (1, 2, (None, None)),
    # Overlapping start
    (1, 3, (2, 3)),
    # Overlapping start and end
    (1, 5, (2, 4)),
    # Exactly the same
    (2, 4, (2, 4)),
    # Overlapping end
    (3, 5, (3, 4)),
    # Right after
    (4, 5, (None, None)),
    # After
    (5, 6, (None, None)),
))
def test_get_overlap(start_hour, end_hour, expected_overlap):
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


@pytest.mark.parametrize('skip_self', (
    (True),
    (False),
))
def test_get_overlaps_self(dummy_occurrence, skip_self):
    if skip_self:
        expected_overlap = (None, None)
    else:
        expected_overlap = (dummy_occurrence.start_dt, dummy_occurrence.end_dt)
    assert dummy_occurrence.get_overlap(dummy_occurrence, skip_self=skip_self) == expected_overlap


@pytest.mark.parametrize(('start_hour', 'end_hour', 'expected'), (
    # Before
    (0, 1, False),
    # Right before
    (1, 2, False),
    # Overlapping start
    (1, 3, True),
    # Overlapping start and end
    (1, 5, True),
    # Exactly the same
    (2, 4, True),
    # Overlapping end
    (3, 5, True),
    # Right after
    (4, 5, False),
    # After
    (5, 6, False),
))
def test_overlaps(start_hour, end_hour, expected):
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


def test_overlaps_self(dummy_occurrence, bool_flag):
    assert dummy_occurrence.overlaps(dummy_occurrence, skip_self=bool_flag) == (not bool_flag)
