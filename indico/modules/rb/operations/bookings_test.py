# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime, timedelta

import pytest

from flask import session

from indico.modules.rb.models.reservations import RepeatFrequency


def test_bookings_are_split_on_time_changes(create_reservation):
    from indico.modules.rb.operations.bookings import should_split_booking

    start_dt = datetime.today().replace(hour=8, minute=30) - timedelta(days=3)
    end_dt = datetime.today().replace(hour=17, minute=30) + timedelta(days=3)
    reservation = create_reservation(start_dt=start_dt,
                                     end_dt=end_dt,
                                     repeat_frequency=RepeatFrequency.DAY,
                                     recurrence_weekdays=None)
    new_booking_data = {
        'start_dt': start_dt, 'end_dt': end_dt,
        'repeat_frequency': reservation.repeat_frequency,
        'repeat_interval': reservation.repeat_interval,
        'recurrence_weekdays': reservation.recurrence_weekdays
    }

    assert not should_split_booking(reservation, new_booking_data)
    assert not should_split_booking(reservation, dict(new_booking_data, end_dt=end_dt + timedelta(days=5)))
    assert should_split_booking(reservation, dict(new_booking_data, start_dt=start_dt.replace(hour=9)))
    assert should_split_booking(reservation, dict(new_booking_data, end_dt=end_dt.replace(hour=20)))
    assert should_split_booking(reservation, dict(new_booking_data, repeat_frequency=RepeatFrequency.NEVER))
    assert should_split_booking(reservation, dict(new_booking_data, repeat_interval=2))


@pytest.mark.parametrize('hour', (0, 13, 19))
@pytest.mark.parametrize(('start_dt', 'end_dt'), (
    (datetime(2026, 11, 17, hour=8, minute=30), datetime(2026, 11, 17, hour=17, minute=30) + timedelta(days=5)),
    (datetime(2026, 11, 17, hour=8, minute=30), datetime(2026, 11, 17, hour=17, minute=30) + timedelta(days=1)),
))
def test_ongoing_bookings_are_not_split(create_reservation, freeze_time, hour, start_dt, end_dt):
    from indico.modules.rb.operations.bookings import split_booking

    freeze_time(datetime(2026, 11, 17, hour))
    reservation = create_reservation(start_dt=start_dt, end_dt=end_dt, repeat_frequency=RepeatFrequency.DAY)
    assert split_booking(reservation, {}, extra_fields={}) is None


@pytest.mark.parametrize('hour', (0, 13, 19))
@pytest.mark.usefixtures('request_context', 'smtp')
def test_past_booking_occurrences_are_cancelled(dummy_user, create_reservation, freeze_time, hour):
    from indico.modules.rb.operations.bookings import split_booking
    session.set_session_user(dummy_user)

    freeze_time(datetime(2026, 11, 17, hour))
    start_dt = datetime.today().replace(hour=8, minute=30) - timedelta(days=2)
    end_dt = datetime.today().replace(hour=17, minute=30) + timedelta(days=4)
    reservation = create_reservation(start_dt=start_dt, end_dt=end_dt, repeat_frequency=RepeatFrequency.DAY)
    new_booking_data = {
        'booking_reason': 'test reason',
        'booked_for_user': dummy_user,
        'start_dt': start_dt,
        'end_dt': end_dt,
        'repeat_frequency': RepeatFrequency.DAY,
        'repeat_interval': reservation.repeat_interval
    }
    new_reservation = split_booking(
        reservation,
        new_booking_data,
        extra_fields={},
    )

    number_of_cancelled_occurrences = len([occ for occ in reservation.occurrences if occ.is_cancelled])
    number_of_new_occurrences = len(list(new_reservation.occurrences))
    assert number_of_cancelled_occurrences == 0
    if hour == 0:
        assert number_of_new_occurrences == 5
    else:
        assert number_of_new_occurrences == 4
