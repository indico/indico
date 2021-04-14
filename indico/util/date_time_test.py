# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime, timedelta

import pytest
from pytz import timezone

from indico.util.date_time import as_utc, format_human_timedelta, iterdays, strftime_all_years


@pytest.mark.parametrize(('delta', 'granularity', 'expected'), (
    (timedelta(days=0, hours=0,  minutes=0,  seconds=0), 'seconds', '0 seconds'),
    (timedelta(days=0, hours=0,  minutes=0,  seconds=0), 'minutes', '0 minutes'),
    (timedelta(days=0, hours=0,  minutes=0,  seconds=0), 'hours',   '0 hours'),
    (timedelta(days=0, hours=0,  minutes=0,  seconds=0), 'days',    '0 days'),
    (timedelta(days=0, hours=0,  minutes=0,  seconds=5), 'seconds', '5 seconds'),
    (timedelta(days=0, hours=0,  minutes=0,  seconds=5), 'minutes', '5 seconds'),
    (timedelta(days=0, hours=0,  minutes=1,  seconds=5), 'seconds', '1m 5s'),
    (timedelta(days=0, hours=0,  minutes=1,  seconds=5), 'minutes', '1 minute'),
    (timedelta(days=0, hours=0,  minutes=1,  seconds=5), 'hours',   '1 minute'),
    (timedelta(days=0, hours=1,  minutes=10, seconds=0), 'hours',   '1 hour'),
    (timedelta(days=0, hours=1,  minutes=30, seconds=0), 'minutes', '1h 30m'),
    (timedelta(days=1, hours=1,  minutes=0,  seconds=0), 'minutes', '1d 1h'),
    (timedelta(days=1, hours=1,  minutes=10, seconds=0), 'minutes', '1d 1h 10m'),
    (timedelta(days=1, hours=1,  minutes=10, seconds=0), 'hours',   '1d 1h'),
    (timedelta(days=1, hours=1,  minutes=0,  seconds=0), 'days',    '1 day'),
    (timedelta(days=1, hours=12, minutes=0,  seconds=0), 'days',    '1 day'),
    (timedelta(days=2, hours=0,  minutes=0,  seconds=0), 'days',    '2 days'),
    (timedelta(days=7, hours=0,  minutes=0,  seconds=0), 'days',    '7 days')
))
def test_format_human_timedelta(delta, granularity, expected):
    assert format_human_timedelta(delta, granularity) == expected


@pytest.mark.parametrize(('dt', 'fmt', 'expected'), (
    (datetime(2015, 11, 12, 17, 30), '%Y-%m-%d', '2015-11-12'),
    (datetime(1015, 11, 12, 17, 30), '%Y-%m-%d %H:%M', '1015-11-12 17:30'),
))
def test_strftime_all_years(dt, fmt, expected):
    assert strftime_all_years(dt, fmt) == expected


dt = datetime
tz = timezone('Europe/Zurich')
iterdays_test_data = (
    (dt(2015, 1, 1, 10, 30).date(), dt(2015, 1, 1, 12, 30), True, None, None, 1),
    (dt(2015, 1, 1, 10, 30), dt(2014, 1, 1, 12, 30), True, None, None, 0),
    (dt(2015, 1, 1, 10, 30), dt(2015, 1, 1, 12, 30), True, None, None, 1),
    (dt(2017, 10, 13), dt(2017, 10, 19), True, None, None, 5),
    (dt(2017, 10, 13), dt(2017, 10, 19), False, None, None, 7),
    (dt(2017, 10, 13), dt(2017, 10, 19), True, [dt(2017, 10, 17).date()], None, 1),
    (dt(2017, 10, 13), dt(2017, 10, 19), True, [dt(2017, 10, 14).date()], None, 0),
    (dt(2017, 10, 13), dt(2017, 10, 19), False, [dt(2017, 10, 14).date()], None, 1),
    (dt(2017, 10, 13), dt(2017, 10, 19), False, None, [dt(2017, 10, 14).date(), dt(2017, 10, 16).date()], 5),
    (dt(2017, 10, 13), dt(2017, 10, 19), False, [dt(2017, 10, 15).date()], [dt(2017, 10, 14).date()], 1),
    (dt(2017, 10, 28, 10, 30), dt(2017, 10, 31, 12, 30), True, None, [dt(2017, 10, 28, 10, 30)], 2),
    (as_utc(dt(2017, 10, 28)).astimezone(tz), as_utc(dt(2017, 10, 31)).astimezone(tz), True, None, None, 2),
    (as_utc(dt(2017, 3, 26)).astimezone(tz), as_utc(dt(2017, 3, 28)).astimezone(tz), True, None, None, 2),
)


@pytest.mark.parametrize(('from_', 'to', 'skip_weekends', 'day_whitelist', 'day_blacklist', 'expected'),
                         iterdays_test_data)
def test_iterdays(from_, to, skip_weekends, day_whitelist, day_blacklist, expected):
    assert len(list(iterdays(from_, to, skip_weekends, day_whitelist, day_blacklist))) == expected
