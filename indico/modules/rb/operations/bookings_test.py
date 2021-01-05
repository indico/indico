# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime, timedelta

import pytest

from indico.modules.rb.models.reservations import RepeatFrequency


pytest_plugins = 'indico.modules.rb.testing.fixtures'


def test_bookings_are_split_on_time_changes(create_reservation):
    from indico.modules.rb.operations.bookings import should_split_booking

    start_dt = datetime.today().replace(hour=8, minute=30) - timedelta(days=3)
    end_dt = datetime.today().replace(hour=17, minute=30) + timedelta(days=3)
    reservation = create_reservation(start_dt=start_dt, end_dt=end_dt, repeat_frequency=RepeatFrequency.DAY)
    new_booking_data = {'start_dt': start_dt, 'end_dt': end_dt, 'repeat_frequency': reservation.repeat_frequency,
                        'repeat_interval': reservation.repeat_interval}

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
    assert split_booking(reservation, {}) is None


def past_booking_occurrences_are_cancelled(dummy_user, create_reservation):
    from indico.modules.rb.operations.bookings import split_booking

    start_dt = datetime.today().replace(hour=8, minutes=30) - timedelta(days=2)
    end_dt = datetime.today().replace(hour=17, minutes=30) + timedelta(days=4)
    reservation = create_reservation(start_dt=start_dt, end_dt=end_dt, repeat_frequency=RepeatFrequency.DAY)
    new_reservation = split_booking(reservation, {
        'booking_reason': 'test reason',
        'booked_for_user': dummy_user,
        'start_dt': start_dt,
        'end_dt': end_dt,
        'repeat_frequency': RepeatFrequency.DAY,
        'repeat_interval': reservation.repeat_interval
    })

    number_of_cancelled_occurrences = [occ for occ in reservation.occurrences if occ.is_cancelled]
    assert number_of_cancelled_occurrences == 2
    assert len(new_reservation.occurrences) == 4
