# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from collections import defaultdict
from datetime import datetime
from itertools import chain

import dateutil.parser

from indico.modules.rb import rb_settings
from indico.modules.rb.models.reservations import RepeatFrequency
from indico.modules.rb.tasks import roombooking_end_notifications, roombooking_occurrences


pytest_plugins = 'indico.modules.rb.testing.fixtures'

settings = {
    'notification_before_days': 2,
    'notification_before_days_weekly': 5,
    'notification_before_days_monthly': 7,
    'end_notification_daily': 1,
    'end_notification_weekly': 3,
    'end_notification_monthly': 7
}

users = {
    'x': {'first_name': 'Mister', 'last_name': 'Evil'},
    'y': {'first_name': 'Doctor', 'last_name': 'No'}
}

rooms = {
    'a': {
        'notification_before_days': None,
        'notification_before_days_weekly': None,
        'notification_before_days_monthly': None,
        'end_notification_daily': None,
        'end_notification_weekly': None,
        'end_notification_monthly': None
    },
    'b': {
        'notification_before_days': 10,
        'notification_before_days_weekly': 11,
        'notification_before_days_monthly': 12,
        'end_notification_daily': 2,
        'end_notification_weekly': 4,
        'end_notification_monthly': 8
    }
}

reservations = [
    {
        'start_dt': '2017-03-31 15:00',
        'end_dt': '2017-04-10 16:00',
        'repeat_frequency': RepeatFrequency.DAY,
        'room': 'a',
        'user': 'x',
        'notification': '2017-04-03',
    },
    {
        'start_dt': '2017-04-03 12:00',
        'end_dt': '2017-04-03 14:00',
        'repeat_frequency': RepeatFrequency.NEVER,
        'room': 'a',
        'user': 'x',
        'notification': '2017-04-03',
    },
    {
        'start_dt': '2017-03-30 12:00',
        'end_dt': '2017-05-04 14:00',
        'repeat_frequency': RepeatFrequency.WEEK,
        'room': 'a',
        'user': 'x',
        'notification': '2017-04-06',
    },
    {
        'start_dt': '2017-04-08 12:00',
        'end_dt': '2017-05-13 14:00',
        'repeat_frequency': RepeatFrequency.MONTH,
        'room': 'a',
        'user': 'y',
        'notification': '2017-04-08',
    },
    {
        'start_dt': '2017-04-11 12:00',
        'end_dt': '2017-04-11 14:00',
        'repeat_frequency': RepeatFrequency.NEVER,
        'room': 'b',
        'user': 'x',
        'notification': '2017-04-11',  # today + 10
    },
    {
        'start_dt': '2017-04-03 12:00',
        'end_dt': '2017-04-03 14:00',
        'repeat_frequency': RepeatFrequency.NEVER,
        'room': 'b',
        'user': 'x',
        'notification': None,  # room has today+10 not today+1
    },
]

finishing_reservations = [
    {
        'start_dt': '2019-07-08 12:00',
        'end_dt': '2019-07-08 14:00',
        'repeat_frequency': RepeatFrequency.NEVER,
        'room': 'b',
        'user': 'x',
        'end_notification': False
    },
    {
        'start_dt': '2019-07-07 14:00',
        'end_dt': '2019-07-07 14:30',
        'repeat_frequency': RepeatFrequency.NEVER,
        'room': 'a',
        'user': 'x',
        'end_notification': False
    },
    {
        'start_dt': '2019-07-07 14:30',
        'end_dt': '2019-07-09 15:00',
        'repeat_frequency': RepeatFrequency.DAY,
        'room': 'a',
        'user': 'x',
        'end_notification': True
    },
    {
        'start_dt': '2019-07-07 15:00',
        'end_dt': '2019-07-10 15:10',
        'repeat_frequency': RepeatFrequency.DAY,
        'room': 'a',
        'user': 'x',
        'end_notification': False
    },
    {
        'start_dt': '2019-07-07 15:10',
        'end_dt': '2019-07-10 15:20',
        'repeat_frequency': RepeatFrequency.DAY,
        'room': 'b',
        'user': 'y',
        'end_notification': True
    },
    {
        'start_dt': '2019-07-07 15:20',
        'end_dt': '2019-07-11 15:30',
        'repeat_frequency': RepeatFrequency.DAY,
        'room': 'b',
        'user': 'y',
        'end_notification': False
    },
    {
        'start_dt': '2019-07-05 15:30',
        'end_dt': '2019-07-12 15:40',
        'repeat_frequency': RepeatFrequency.WEEK,
        'room': 'b',
        'user': 'y',
        'end_notification': True
    },
    {
        'start_dt': '2019-07-05 15:40',
        'end_dt': '2019-07-15 15:50',
        'repeat_frequency': RepeatFrequency.WEEK,
        'room': 'b',
        'user': 'y',
        'end_notification': True
    },
    {
        'start_dt': '2019-07-05 15:50',
        'end_dt': '2019-07-19 16:00',
        'repeat_frequency': RepeatFrequency.WEEK,
        'room': 'b',
        'user': 'y',
        'end_notification': False
    },
    {
        'start_dt': '2019-07-04 16:00',
        'end_dt': '2019-07-11 16:10',
        'repeat_frequency': RepeatFrequency.WEEK,
        'room': 'a',
        'user': 'x',
        'end_notification': True
    }
]


def test_roombooking_notifications(mocker, create_user, create_room, create_reservation, freeze_time):
    rb_settings.set_multi(settings)
    user_map = {key: create_user(id_, **data) for id_, (key, data) in enumerate(users.iteritems(), 1)}
    room_map = {key: create_room(**data) for key, data in rooms.iteritems()}

    notification_map = defaultdict(dict)
    end_notification_map = defaultdict(dict)
    for data in chain(reservations, finishing_reservations):
        data['start_dt'] = dateutil.parser.parse(data['start_dt'])
        data['end_dt'] = dateutil.parser.parse(data['end_dt'])
        data['booked_for_user'] = user = user_map[data.pop('user')]
        data['room'] = room_map[data['room']]
        notification = data.pop('notification', None)
        end_notification = data.pop('end_notification', None)
        reservation = create_reservation(**data)
        if notification:
            notification_map[user][reservation] = dateutil.parser.parse(notification).date()
        if end_notification is not None:
            end_notification_map[user][reservation] = end_notification

    notify_upcoming_occurrences = mocker.patch('indico.modules.rb.tasks.notify_upcoming_occurrences')
    notify_about_finishing_bookings = mocker.patch('indico.modules.rb.tasks.notify_about_finishing_bookings')
    freeze_time(datetime(2017, 4, 1, 8, 0, 0))
    roombooking_occurrences()
    for (user, occurrences), __ in notify_upcoming_occurrences.call_args_list:
        notifications = notification_map.pop(user)
        for occ in occurrences:
            date = notifications.pop(occ.reservation)
            assert occ.start_dt.date() == date
            assert occ.notification_sent
            past_occs = [x for x in occ.reservation.occurrences if x.start_dt.date() < date.today()]
            future_occs = [x for x in occ.reservation.occurrences if x.start_dt.date() > date.today() and x != occ]
            assert not any(x.notification_sent for x in past_occs)
            if occ.reservation.repeat_frequency == RepeatFrequency.DAY:
                assert all(x.notification_sent for x in future_occs)
            else:
                assert not any(x.notification_sent for x in future_occs)
        assert not notifications  # no extra notifications
    assert not notification_map  # no extra users

    freeze_time(datetime(2019, 7, 8, 8, 0, 0))
    roombooking_end_notifications()
    for (user, user_finishing_reservations), __ in notify_about_finishing_bookings.call_args_list:
        end_notifications = end_notification_map.pop(user)
        for reservation in user_finishing_reservations:
            should_be_sent = end_notifications.pop(reservation)
            assert reservation.end_notification_sent == should_be_sent
        assert all(not r.end_notification_sent for r in end_notifications)
    assert not end_notification_map
