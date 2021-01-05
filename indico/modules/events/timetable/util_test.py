# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import date, datetime

import pytest
from pytz import utc

from indico.modules.events.timetable.util import find_latest_entry_end_dt


@pytest.mark.parametrize(('event_start_dt', 'event_end_dt', 'day', 'valid'), (
    (datetime(2016, 1, 2, tzinfo=utc), datetime(2016, 1, 4, 23, 59, tzinfo=utc), date(2016, 1, 2), True),
    (datetime(2016, 1, 2, tzinfo=utc), datetime(2016, 1, 4, 23, 59, tzinfo=utc), date(2016, 1, 3), True),
    (datetime(2016, 1, 2, tzinfo=utc), datetime(2016, 1, 4, 23, 59, tzinfo=utc), date(2016, 1, 4), True),
    (datetime(2016, 1, 2, tzinfo=utc), datetime(2016, 1, 4, 23, 59, tzinfo=utc), date(2016, 1, 1), False),
    (datetime(2016, 1, 2, tzinfo=utc), datetime(2016, 1, 4, 23, 59, tzinfo=utc), date(2016, 1, 5), False),
    (datetime(2016, 1, 2, tzinfo=utc), datetime(2016, 1, 4, 23, 59, tzinfo=utc), None,             False),
))
def test_find_latest_entry_end_dt_valid_day(dummy_event, event_start_dt, event_end_dt, day, valid):
    dummy_event.start_dt = event_start_dt
    dummy_event.end_dt = event_end_dt
    if not valid:
        with pytest.raises(ValueError):
            find_latest_entry_end_dt(obj=dummy_event, day=day)
