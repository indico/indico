# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import date, datetime, time

import dateutil.parser
import pytest

from indico.modules.rb.models.reservations import ConflictingOccurrences, RepeatFrequency
from indico.modules.rb.models.room_bookable_hours import BookableHours
from indico.testing.util import bool_matrix


@pytest.mark.parametrize(('is_admin', 'is_owner', 'fits', 'success'), bool_matrix('...', expect=any))
def test_enforcement(db, dummy_room, create_user, create_reservation, is_admin, is_owner, fits, success):
    user = create_user(123, rb_admin=True)
    if is_owner:
        dummy_room.update_principal(user, full_access=True)
    dummy_room.bookable_hours = [BookableHours(start_time=time(12), end_time=time(14))]
    db.session.flush()
    booking_hours = (time(12), time(13)) if fits else (time(8), time(9))

    _create = lambda: create_reservation(start_dt=datetime.combine(date(2024, 7, 15), booking_hours[0]),
                                         end_dt=datetime.combine(date(2024, 7, 15), booking_hours[1]),
                                         created_by_user=user,
                                         allow_admin=is_admin)

    if success:
        _create()
    else:
        with pytest.raises(ConflictingOccurrences):
            _create()


@pytest.mark.parametrize(('start_dt', 'end_dt', 'success'), (
    ('2024-07-01 10:00', '2024-07-01 11:00', False),  # outside bookable hours
    ('2024-07-01 11:30', '2024-07-01 11:45', True),   # matching global bookable hours
    ('2024-07-01 11:00', '2024-07-08 12:00', True),   # matching global bookable hours
    ('2024-07-01 12:00', '2024-07-03 14:00', False),  # one day outside bookable hours
    ('2024-07-03 12:00', '2024-07-03 14:00', True),   # matching day bookable hours
    ('2024-07-02 11:00', '2024-07-03 14:00', True),   # matching combination of global and day bookable hours
))
def test_weekdays(db, dummy_room, create_user, create_reservation, start_dt, end_dt, success):
    user = create_user(123, rb_admin=True)
    dummy_room.bookable_hours = [
        # 11-12 every day, 12-14 tuesdays+wednesdays
        BookableHours(start_time=time(11), end_time=time(12), weekday=None),
        BookableHours(start_time=time(12), end_time=time(14), weekday='tue'),
        BookableHours(start_time=time(12), end_time=time(14), weekday='wed')
    ]
    db.session.flush()
    start_dt = dateutil.parser.parse(start_dt)
    end_dt = dateutil.parser.parse(end_dt)
    repeat_frequency = RepeatFrequency.NEVER if start_dt.date() == end_dt.date else RepeatFrequency.DAY
    _create = lambda: create_reservation(start_dt=start_dt, end_dt=end_dt, repeat_frequency=repeat_frequency,
                                         created_by_user=user)

    if success:
        _create()
    else:
        with pytest.raises(ConflictingOccurrences):
            _create()
