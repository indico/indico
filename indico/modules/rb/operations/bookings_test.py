# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime, timedelta
from unittest.mock import patch

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


@pytest.mark.parametrize(('start_dt', 'end_dt'), (
    (datetime.today().replace(hour=8, minute=30), datetime.today().replace(hour=17, minute=30) + timedelta(days=5)),
    (datetime.today().replace(hour=8, minute=30), datetime.today().replace(hour=17, minute=30) + timedelta(days=1)),
))
def test_ongoing_bookings_are_not_split(create_reservation, start_dt, end_dt):
    from indico.modules.rb.operations.bookings import split_booking

    reservation = create_reservation(start_dt=start_dt, end_dt=end_dt, repeat_frequency=RepeatFrequency.DAY)
    assert split_booking(reservation, {}, extra_fields={}) is None


@pytest.mark.usefixtures('request_context')
def test_past_booking_occurrences_are_cancelled(dummy_user, create_reservation):
    from indico.modules.rb.operations.bookings import split_booking

    session['_user_id'] = dummy_user.id

    datetime_now = datetime.today().replace(hour=12, minute=0, second=0, microsecond=0)
    start_dt = datetime_now.replace(hour=8, minute=30) - timedelta(days=2)
    end_dt = datetime_now.replace(hour=17, minute=30) + timedelta(days=4)

    reservation = create_reservation(start_dt=start_dt, end_dt=end_dt, repeat_frequency=RepeatFrequency.DAY)
    new_booking_data = {
        'booking_reason': 'test reason',
        'booked_for_user': dummy_user,
        'start_dt': start_dt,
        'end_dt': end_dt,
        'repeat_frequency': RepeatFrequency.DAY,
        'repeat_interval': reservation.repeat_interval
    }

    class MockDatetime:
        @staticmethod
        def now():
            return datetime_now

        @staticmethod
        def combine(date_obj, time_obj):
            return datetime.combine(date_obj, time_obj)

    class MockDate:
        @staticmethod
        def today():
            return datetime_now.date()

    with patch('indico.core.notifications.send_email'), \
        patch('indico.modules.rb.operations.bookings.datetime', MockDatetime), \
        patch('indico.modules.rb.operations.bookings.date', MockDate), \
        patch('indico.modules.rb.models.reservation_occurrences.ReservationOccurrence.cancel') as mock_cancel:

        new_reservation = split_booking(
            reservation,
            new_booking_data,
            extra_fields={},
        )

        assert mock_cancel.called
        assert mock_cancel.call_count == 4

    new_occurrences_count = len(list(new_reservation.occurrences))
    assert new_occurrences_count == 4