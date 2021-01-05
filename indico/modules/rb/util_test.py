# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from datetime import date, datetime, time, timedelta

import pytest
import pytz

from indico.modules.rb import rb_settings
from indico.modules.rb.models.reservations import ReservationState
from indico.modules.rb.util import (get_booking_params_for_event, get_prebooking_collisions, rb_check_user_access,
                                    rb_is_admin)
from indico.testing.util import bool_matrix


pytest_plugins = ('indico.modules.rb.testing.fixtures', 'indico.modules.events.timetable.testing.fixtures')


@pytest.mark.parametrize(('is_rb_admin', 'acl_empty', 'in_acl', 'expected'), bool_matrix('...', expect=any))
def test_rb_check_user_access(db, mocker, dummy_user, dummy_group, is_rb_admin, acl_empty, in_acl, expected):
    if is_rb_admin:
        mocker.patch('indico.modules.rb.util.rb_is_admin', return_value=True)
    if not acl_empty:
        rb_settings.acls.add_principal('authorized_principals', dummy_group)
    if in_acl:
        rb_settings.acls.add_principal('authorized_principals', dummy_user)
    assert rb_check_user_access(dummy_user) == expected


@pytest.mark.parametrize(('is_admin', 'is_rb_admin', 'expected'), bool_matrix('..', expect=any))
def test_rb_is_admin(create_user, is_admin, is_rb_admin, expected):
    user = create_user(1, admin=is_admin, rb_admin=is_rb_admin)
    assert rb_is_admin(user) == expected


@pytest.mark.parametrize(('start_dt', 'end_dt', 'expected_params'), (
    # single-day event
    (datetime(2019, 8, 16, 10, 0), datetime(2019, 8, 16, 13, 0), {'recurrence': 'single',
                                                                  'interval': 'week',
                                                                  'number': 1,
                                                                  'sd': '2019-08-16',
                                                                  'ed': None,
                                                                  'st': '10:00',
                                                                  'et': '13:00'}),
    # multi-day event
    (datetime(2019, 8, 16, 10, 0), datetime(2019, 8, 18, 13, 0), {'recurrence': 'daily',
                                                                  'interval': 'week',
                                                                  'number': 1,
                                                                  'sd': '2019-08-16',
                                                                  'ed': '2019-08-18',
                                                                  'st': '10:00',
                                                                  'et': '13:00'}),
    # end time < start time
    (datetime(2019, 8, 16, 16, 0), datetime(2019, 8, 18, 13, 0), {'sd': '2019-08-16'})
))
def test_get_booking_params_for_event_same_times(create_event, dummy_room, start_dt, end_dt, expected_params):
    start_dt = pytz.utc.localize(start_dt)
    end_dt = pytz.utc.localize(end_dt)
    event = create_event(start_dt=start_dt, end_dt=end_dt, room=dummy_room)
    params = get_booking_params_for_event(event)
    assert params == {
        'type': 'same_times',
        'params': dict({
            'link_id': event.id,
            'link_type': 'event',
            'text': '#{}'.format(dummy_room.id),
        }, **expected_params)
    }


@pytest.mark.parametrize(('start_time', 'end_time', 'expected_params'), (
    # start time < end time
    (time(10), time(13), {'interval': 'week', 'number': 1, 'recurrence': 'single', 'st': '10:00', 'et': '13:00'}),
    # end time < start time
    (time(15), time(13), {}),
))
def test_get_booking_params_for_event_multiple_times(create_event, create_contribution, create_entry, dummy_room,
                                                     start_time, end_time, expected_params):
    start_dt = pytz.utc.localize(datetime.combine(date(2019, 8, 16), start_time))
    end_dt = pytz.utc.localize(datetime.combine(date(2019, 8, 18), end_time))
    event = create_event(start_dt=start_dt, end_dt=end_dt, room=dummy_room)
    c1 = create_contribution(event, 'C1', timedelta(minutes=30))
    c2 = create_contribution(event, 'C2', timedelta(minutes=120))
    c3 = create_contribution(event, 'C3', timedelta(minutes=30))
    create_entry(c1, pytz.utc.localize(datetime(2019, 8, 17, 9, 0)))
    create_entry(c2, pytz.utc.localize(datetime(2019, 8, 17, 18, 0)))
    create_entry(c3, pytz.utc.localize(datetime(2019, 8, 17, 19, 0)))
    params = get_booking_params_for_event(event)
    assert params == {
        'type': 'mixed_times',
        'params': {
            'link_type': 'event',
            'link_id': event.id,
            'text': '#{}'.format(dummy_room.id),
        },
        'time_info': [
            (date(2019, 8, 16), dict({'sd': '2019-08-16'}, **expected_params)),
            # this day has timetable entries -> not using the event defaults
            (date(2019, 8, 17), {'interval': 'week', 'number': 1, 'recurrence': 'single',
                                 'sd': '2019-08-17', 'st': '09:00', 'et': '20:00'}),
            (date(2019, 8, 18), dict({'sd': '2019-08-18'}, **expected_params))
        ]
    }


def test_get_booking_params_timezone(create_event):
    chicago_tz = pytz.timezone('America/Chicago')
    start_dt = chicago_tz.localize(datetime(2019, 8, 16, 8, 0)).astimezone(pytz.utc)
    end_dt = chicago_tz.localize(datetime(2019, 8, 18, 22, 0)).astimezone(pytz.utc)
    event = create_event(start_dt=start_dt, end_dt=end_dt, timezone='America/Chicago')

    assert get_booking_params_for_event(event) == {
        'type': 'same_times',
        'params': {
            'sd': '2019-08-16',
            'st': '08:00',
            'ed': '2019-08-18',
            'et': '22:00',
            'interval': 'week',
            'number': 1,
            'recurrence': 'daily',
            'link_id': event.id,
            'link_type': 'event',
            'text': None
        }
    }


def test_get_prebooking_collisions(create_reservation, dummy_user, freeze_time):
    freeze_time(datetime(2020, 3, 20, 12, 0, 0))
    start_dt = datetime(2020, 4, 1, 9, 0)
    end_dt = datetime(2020, 4, 1, 12, 0)

    res1 = create_reservation(start_dt=start_dt, end_dt=end_dt, state=ReservationState.pending)
    res2 = create_reservation(start_dt=start_dt, end_dt=end_dt, state=ReservationState.pending)
    create_reservation(start_dt=end_dt, end_dt=datetime(2020, 4, 1, 15, 0), state=ReservationState.pending)
    res_cancelled = create_reservation(start_dt=start_dt, end_dt=end_dt, state=ReservationState.pending)
    res_cancelled.cancel(dummy_user, silent=True)
    res_rejected = create_reservation(start_dt=start_dt, end_dt=end_dt, state=ReservationState.pending)
    res_rejected.reject(dummy_user, 'Testing', silent=True)

    collisions = get_prebooking_collisions(res1)
    assert collisions == [res2.occurrences.one()]
