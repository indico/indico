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

from collections import defaultdict
from datetime import datetime

import dateutil.parser

from indico.modules.rb import rb_settings
from indico.modules.rb.models.reservations import RepeatFrequency
from indico.modules.rb.tasks import roombooking_occurrences

pytest_plugins = 'indico.modules.rb.testing.fixtures'


def test_roombooking_occurrences(mocker, create_user, create_room, create_reservation, freeze_time):
    settings = {
        'notification_before_days': 2,
        'notification_before_days_weekly': 5,
        'notification_before_days_monthly': 7,
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
        },
        'b': {
            'notification_before_days': 10,
            'notification_before_days_weekly': 11,
            'notification_before_days_monthly': 12,
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
            'notification': '2017-04-03'
        },
        {
            'start_dt': '2017-03-30 12:00',
            'end_dt': '2017-05-04 14:00',
            'repeat_frequency': RepeatFrequency.WEEK,
            'room': 'a',
            'user': 'x',
            'notification': '2017-04-06'
        },
        {
            'start_dt': '2017-04-08 12:00',
            'end_dt': '2017-05-13 14:00',
            'repeat_frequency': RepeatFrequency.MONTH,
            'room': 'a',
            'user': 'y',
            'notification': '2017-04-08'
        },
        {
            'start_dt': '2017-04-11 12:00',
            'end_dt': '2017-04-11 14:00',
            'repeat_frequency': RepeatFrequency.NEVER,
            'room': 'b',
            'user': 'x',
            'notification': '2017-04-11'  # today + 10
        },
        {
            'start_dt': '2017-04-03 12:00',
            'end_dt': '2017-04-03 14:00',
            'repeat_frequency': RepeatFrequency.NEVER,
            'room': 'b',
            'user': 'x',
            'notification': None  # room has today+10 not today+1
        },
    ]

    rb_settings.set_multi(settings)
    user_map = {key: create_user(id_, **data) for id_, (key, data) in enumerate(users.iteritems(), 1)}
    room_map = {key: create_room(**data) for key, data in rooms.iteritems()}

    notification_map = defaultdict(dict)
    for data in reservations:
        data['start_dt'] = dateutil.parser.parse(data['start_dt'])
        data['end_dt'] = dateutil.parser.parse(data['end_dt'])
        data['booked_for_user'] = user = user_map[data.pop('user')]
        data['room'] = room_map[data['room']]
        notification = data.pop('notification')
        reservation = create_reservation(**data)
        if notification:
            notification_map[user][reservation] = dateutil.parser.parse(notification).date()

    notify_upcoming_occurrences = mocker.patch('indico.modules.rb.tasks.notify_upcoming_occurrences')
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
