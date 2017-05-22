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

from datetime import timedelta, datetime

import pytest

from indico.util.date_time import format_human_timedelta, strftime_all_years


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
