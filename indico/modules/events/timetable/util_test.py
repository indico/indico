# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from datetime import datetime, date, timedelta

import pytest
from pytz import utc

from indico.modules.events.timetable.util import find_earliest_gap

pytest_plugins = ('indico.modules.events.contributions.testing.fixtures',
                  'indico.modules.events.timetable.testing.fixtures')


@pytest.mark.parametrize(('event_duration_minutes', 'fits'), (
    (60, True),
    (20, True),
    (10, False),
))
def test_find_earliest_gap_no_entries(dummy_event_new, event_duration_minutes, fits):
    dummy_event_new.end_dt = dummy_event_new.start_dt + timedelta(minutes=event_duration_minutes)
    day = dummy_event_new.start_dt.date()
    start_dt = find_earliest_gap(dummy_event_new, day=day, duration=timedelta(minutes=20))
    if fits:
        assert start_dt == dummy_event_new.start_dt
    else:
        assert start_dt is None


@pytest.mark.parametrize(('entry_minutes_offset', 'duration', 'expected_start_dt_minutes_offset'), (
    (0,  20, 20),
    (10, 20, 30),
    (20, 20, 0),
))
def test_find_earliest_gap_with_one_entry(dummy_event_new, dummy_contribution, create_entry,
                                          entry_minutes_offset, duration, expected_start_dt_minutes_offset):
    event_start_dt = dummy_event_new.start_dt
    entry_start_dt = event_start_dt + timedelta(minutes=entry_minutes_offset)
    create_entry(dummy_contribution, start_dt=entry_start_dt)
    start_dt = find_earliest_gap(dummy_event_new, day=event_start_dt.date(), duration=timedelta(minutes=duration))
    assert start_dt - event_start_dt == timedelta(minutes=expected_start_dt_minutes_offset)


def test_find_earliest_gap_with_two_entries(dummy_event_new, create_contribution, create_entry):
    event_start_dt = dummy_event_new.start_dt
    contrib1 = create_contribution("Contrib A", duration=timedelta(minutes=20))
    contrib2 = create_contribution("Contrib B", duration=timedelta(minutes=20))
    create_entry(contrib1, start_dt=event_start_dt)
    entry2 = create_entry(contrib2, start_dt=event_start_dt + timedelta(minutes=10))
    start_dt = find_earliest_gap(dummy_event_new, day=event_start_dt.date(), duration=timedelta(minutes=20))
    assert start_dt == entry2.end_dt


def test_find_earliest_gap_full(dummy_event_new, dummy_contribution, create_entry):
    dummy_event_new.end_dt = dummy_event_new.start_dt + timedelta(minutes=30)
    create_entry(dummy_contribution, start_dt=dummy_event_new.start_dt)
    start_dt = find_earliest_gap(dummy_event_new, day=dummy_event_new.start_dt.date(), duration=timedelta(minutes=20))
    assert start_dt is None


@pytest.mark.parametrize(('event_start_dt', 'event_end_dt', 'day', 'valid'), (
    (datetime(2016, 1, 2, tzinfo=utc), datetime(2016, 1, 4, 23, 59, tzinfo=utc), date(2016, 1, 1), False),
    (datetime(2016, 1, 2, tzinfo=utc), datetime(2016, 1, 4, 23, 59, tzinfo=utc), date(2016, 1, 5), False),
    (datetime(2016, 1, 2, tzinfo=utc), datetime(2016, 1, 4, 23, 59, tzinfo=utc), date(2016, 1, 2), True),
    (datetime(2016, 1, 2, tzinfo=utc), datetime(2016, 1, 4, 23, 59, tzinfo=utc), date(2016, 1, 3), True),
    (datetime(2016, 1, 2, tzinfo=utc), datetime(2016, 1, 4, 23, 59, tzinfo=utc), date(2016, 1, 4), True),
))
def test_find_earliest_gap_valid_day(dummy_event_new, event_start_dt, event_end_dt, day, valid):
    dummy_event_new.start_dt = event_start_dt
    dummy_event_new.end_dt = event_end_dt
    data = {'day': day, 'duration': timedelta(minutes=20)}
    if not valid:
        with pytest.raises(ValueError):
            find_earliest_gap(dummy_event_new, **data)
    else:
        assert find_earliest_gap(dummy_event_new, **data).date() == day


@pytest.mark.parametrize(('event_start_dt', 'event_end_dt', 'day', 'valid'), (
    (datetime(2016, 1, 2, tzinfo=utc), datetime(2016, 1, 4, 23, 59, tzinfo=utc), date(2016, 1, 2), True),
    (datetime(2016, 1, 2, tzinfo=utc), datetime(2016, 1, 4, 23, 59, tzinfo=utc), date(2016, 1, 3), True),
    (datetime(2016, 1, 2, tzinfo=utc), datetime(2016, 1, 4, 23, 59, tzinfo=utc), date(2016, 1, 4), True),
    (datetime(2016, 1, 2, tzinfo=utc), datetime(2016, 1, 4, 23, 59, tzinfo=utc), date(2016, 1, 1), False),
    (datetime(2016, 1, 2, tzinfo=utc), datetime(2016, 1, 4, 23, 59, tzinfo=utc), date(2016, 1, 5), False),
    (datetime(2016, 1, 2, tzinfo=utc), datetime(2016, 1, 4, 23, 59, tzinfo=utc), None,             False),
))
def test_find_latest_entry_end_dt_valid_day(dummy_event_new, event_start_dt, event_end_dt, day, valid):
    dummy_event_new.start_dt = event_start_dt
    dummy_event_new.end_dt = event_end_dt
    if not valid:
        with pytest.raises(ValueError):
            find_latest_entry_end_dt(obj=dummy_event_new, day=day)
