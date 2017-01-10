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

from datetime import datetime, date

import pytest
from pytz import utc

from indico.modules.events.timetable.util import find_latest_entry_end_dt

pytest_plugins = ('indico.modules.events.timetable.testing.fixtures',)


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
