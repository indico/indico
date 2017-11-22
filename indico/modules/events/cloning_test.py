# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from datetime import datetime

import pytest
from pytz import timezone

from indico.modules.events.management.controllers.cloning import (CloneCalculator, IntervalCloneCalculator,
                                                                  PatternCloneCalculator)
from indico.modules.events.management.forms import CloneRepeatIntervalForm, CloneRepeatPatternForm
from indico.util.date_time import relativedelta


@pytest.mark.parametrize(('start_dt', 'delta', 'stop_criterion', 'num_times', 'until_dt',
                          'expected_dates', 'expected_flag'), (
    (datetime(2017, 2, 28, 3, 0, 0), relativedelta(years=1), 'num_times', 2, None,
     [datetime(2017, 2, 28, 3, 0, 0), datetime(2018, 2, 28, 3, 0, 0)], False),
    (datetime(2017, 2, 28, 3, 0, 0), relativedelta(months=1), 'num_times', 3, None,
     [datetime(2017, 2, 28, 3, 0, 0), datetime(2017, 3, 31, 3, 0, 0), datetime(2017, 4, 30, 3, 0, 0)], True),
    (datetime(2017, 2, 27, 3, 0, 0), relativedelta(months=1), 'num_times', 3, None,
     [datetime(2017, 2, 27, 3, 0, 0), datetime(2017, 3, 27, 3, 0, 0), datetime(2017, 4, 27, 3, 0, 0)], False),
    (datetime(2017, 2, 28, 3, 0, 0), relativedelta(months=1), 'day', None, datetime(2017, 4, 30, 3, 0, 0),
     [datetime(2017, 2, 28, 3, 0, 0), datetime(2017, 3, 31, 3, 0, 0)], True),
    (datetime(2017, 2, 28, 3, 0, 0), relativedelta(weeks=2), 'num_times', 3, None,
     [datetime(2017, 2, 28, 3, 0, 0), datetime(2017, 3, 14, 3, 0, 0), datetime(2017, 3, 28, 3, 0, 0)], False),
    (datetime(2017, 2, 28, 3, 0, 0), relativedelta(days=1), 'day', None, datetime(2017, 3, 2, 3, 0, 0),
     [datetime(2017, 2, 28, 3, 0, 0), datetime(2017, 3, 1, 3, 0, 0), datetime(2017, 3, 2, 3, 0, 0)], False)
))
def test_interval_clone(start_dt, delta, stop_criterion, num_times, until_dt,
                        expected_dates, expected_flag, dummy_event):
    dummy_event.timezone = 'Europe/Zurich'
    clone_calculator = IntervalCloneCalculator(dummy_event)
    form = CloneRepeatIntervalForm(dummy_event, csrf_enabled=False, recurrence=delta, stop_criterion=stop_criterion,
                                   num_times=num_times)
    expected_dates = [dummy_event.tzinfo.localize(dt) for dt in expected_dates]
    form.start_dt.data = dummy_event.tzinfo.localize(start_dt)
    form.until_dt.data = dummy_event.tzinfo.localize(until_dt) if until_dt else None
    dates, last_day_of_the_month = clone_calculator._calculate(form)
    assert last_day_of_the_month is expected_flag
    assert dates == expected_dates


@pytest.mark.parametrize(('start_dt', 'week_day', 'num_months',  'stop_criterion', 'num_times', 'until_dt',
                          'expected_dates', 'expected_flag'), (
    (datetime(2017, 12, 7, 3, 0, 0), (1, 0), 1, 'num_times', 2, None,
     [datetime(2018, 1, 1, 3, 0, 0), datetime(2018, 2, 5, 3, 0, 0)], False),
    (datetime(2018, 1, 1, 3, 0, 0), (1, 0), 1, 'num_times', 2, None,
     [datetime(2018, 1, 1, 3, 0, 0), datetime(2018, 2, 5, 3, 0, 0)], False),
    (datetime(2017, 11, 25, 3, 0, 0), (4, 6), 1, 'num_times', 3, None,
     [datetime(2017, 11, 26, 3, 0, 0), datetime(2017, 12, 24, 3, 0, 0), datetime(2018, 1, 28, 3, 0, 0)], False),
    (datetime(2017, 11, 25, 3, 0, 0), (-1, 6), 1, 'num_times', 3, None,
     [datetime(2017, 11, 26, 3, 0, 0), datetime(2017, 12, 31, 3, 0, 0), datetime(2018, 1, 28, 3, 0, 0)], False),
    (datetime(2017, 7, 19, 3, 0, 0), (3, 2), 2, 'day', None, datetime(2017, 11, 30, 3, 0, 0),
     [datetime(2017, 7, 19, 3, 0, 0), datetime(2017, 9, 20, 3, 0, 0), datetime(2017, 11, 15, 3, 0, 0)], False),

))
def test_pattern_clone(start_dt, week_day, num_months, stop_criterion, num_times, until_dt, expected_dates,
                       expected_flag, dummy_event):
    dummy_event.timezone = 'Europe/Zurich'
    clone_calculator = PatternCloneCalculator(dummy_event)
    form = CloneRepeatPatternForm(dummy_event, csrf_enabled=False, week_day=week_day, num_months=num_months,
                                  stop_criterion=stop_criterion, num_times=num_times, until_dt=until_dt)
    expected_dates = [dummy_event.tzinfo.localize(dt) for dt in expected_dates]
    form.start_dt.data = dummy_event.tzinfo.localize(start_dt)
    dates, last_day_of_the_month = clone_calculator._calculate(form)
    assert last_day_of_the_month is expected_flag
    assert dates == expected_dates


@pytest.mark.parametrize(('event_date', 'event_timezone'), (
    (datetime(2018,  3, 25, 2, 0, 0), 'Europe/Zurich'),
    (datetime(2018, 10, 25, 3, 0, 0), 'Europe/Zurich')
))
def test_dst_change(event_date, event_timezone, dummy_event):
    dummy_event.timezone = event_timezone
    clone_calulator = CloneCalculator(dummy_event)
    event_local_date = clone_calulator._tzify([event_date])[0]
    assert event_local_date == timezone(event_timezone).localize(event_date)
