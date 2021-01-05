# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from datetime import datetime, timedelta
from io import BytesIO

import pytest

from indico.core.errors import UserValueError
from indico.modules.events.contributions.util import import_contributions_from_csv
from indico.util.date_time import as_utc


def _check_importer_exception(event, csv):
    with pytest.raises(UserValueError) as e:
        import_contributions_from_csv(event, BytesIO(csv))
    return e.value


def test_import_contributions(dummy_event, dummy_user):
    dummy_event.start_dt = as_utc(datetime(2017, 11, 27, 8, 0, 0))
    dummy_event.end_dt = as_utc(datetime(2017, 11, 27, 12, 0, 0))

    csv = b'\n'.join([b'2017-11-27T08:00,10,First contribution,,,,',
                      b',,Second contribution,John,Doe,ACME Inc.,jdoe@example.com',
                      b'2017-11-27T08:30,15,Third contribution,Guinea Albert,Pig,,1337@example.com'])

    contributions, changes = import_contributions_from_csv(dummy_event, BytesIO(csv))
    assert len(contributions) == 3

    assert contributions[0].start_dt == dummy_event.start_dt
    assert contributions[0].duration == timedelta(minutes=10)
    assert contributions[0].title == 'First contribution'
    assert len(contributions[0].speakers) == 0

    assert contributions[1].start_dt is None
    assert contributions[1].duration == timedelta(minutes=20)
    assert contributions[1].title == 'Second contribution'
    speakers = contributions[1].speakers
    assert len(speakers) == 1
    assert speakers[0].full_name == 'John Doe'
    assert speakers[0].affiliation == 'ACME Inc.'
    assert speakers[0].email == 'jdoe@example.com'

    assert contributions[2].start_dt == as_utc(datetime(2017, 11, 27, 8, 30, 0))
    assert contributions[2].duration == timedelta(minutes=15)
    assert contributions[2].title == 'Third contribution'
    speakers = contributions[2].speakers
    assert len(speakers) == 1
    # name comes from PersonLink, not user
    assert speakers[0].full_name == 'Guinea Albert Pig'
    assert not speakers[0].affiliation
    assert speakers[0].email == '1337@example.com'
    assert speakers[0].person.user == dummy_user

    assert not changes


def test_import_contributions_changes(db, dummy_event, dummy_user):
    original_start_dt = as_utc(datetime(2017, 11, 27, 8, 0, 0))
    original_end_dt = as_utc(datetime(2017, 11, 27, 12, 0, 0))
    dummy_event.start_dt = original_start_dt
    dummy_event.end_dt = original_end_dt

    # Change of end time
    csv = b'\n'.join([b'2017-11-27T08:00,10,First contribution,,,,',
                      b'2017-11-27T08:10:00,10,Second contribution,John,Doe,ACME Inc.,jdoe@example.com',
                      b'2017-11-27T11:30,60,Third contribution,Guinea Albert,Pig,,1337@example.com'])

    contributions, changes = import_contributions_from_csv(dummy_event, BytesIO(csv))
    new_end_dt = as_utc(datetime(2017, 11, 27, 12, 30, 0))
    assert dummy_event.end_dt == new_end_dt
    assert changes == {
        'duration': [(timedelta(hours=4), timedelta(hours=4, minutes=30))],
        'end_dt': [(original_end_dt, new_end_dt)]
    }

    # reset date/time
    dummy_event.start_dt = original_start_dt
    dummy_event.end_dt = original_end_dt

    # Change of start/end date
    csv = b'\n'.join([b'2017-11-26T08:00,10,First contribution,,,,',
                      b'2017-11-27T08:10:00,10,Second contribution,John,Doe,ACME Inc.,jdoe@example.com',
                      b'2017-11-28T11:30,60,Third contribution,Guinea Albert,Pig,,1337@example.com'])

    contributions, changes = import_contributions_from_csv(dummy_event, BytesIO(csv))
    new_start_dt = as_utc(datetime(2017, 11, 26, 8, 0, 0))
    new_end_dt = as_utc(datetime(2017, 11, 28, 12, 30, 0))
    assert dummy_event.start_dt == new_start_dt
    assert dummy_event.end_dt == new_end_dt
    assert len(changes) == 3


def test_import_contributions_errors(db, dummy_event):
    original_start_dt = as_utc(datetime(2017, 11, 27, 8, 0, 0))
    original_end_dt = as_utc(datetime(2017, 11, 27, 12, 0, 0))
    dummy_event.start_dt = original_start_dt
    dummy_event.end_dt = original_end_dt

    e = _check_importer_exception(dummy_event, b',,Test,,,,,')
    assert 'malformed' in str(e)
    assert 'Row 1' in str(e)

    e = _check_importer_exception(dummy_event, b',,,,,,')
    assert 'title' in str(e)

    e = _check_importer_exception(dummy_event, b'2010-23-02T00:00:00,,Test,,,,')
    assert 'parse date' in str(e)

    e = _check_importer_exception(dummy_event, b'2010-02-23T00:00:00,15min,Test,,,,')
    assert 'parse duration' in str(e)

    e = _check_importer_exception(dummy_event, b'2010-02-23T00:00:00,15,Test,Test,Test,Test,foobar')
    assert 'invalid email' in str(e)
