# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

import json

from datetime import date, datetime, time, timedelta
from os import urandom
from pytz import timezone
from random import randint

from indico.modules.rb.models.reservations import RepeatFrequency
from MaKaC.user import Avatar, AvatarHolder, LoginInfo, Group, GroupHolder


def _create_utc_dt(*args):
    return timezone('UTC').localize(datetime(*args))

LIVE_START_DATE = [datetime(2014, 01, 01, 10), datetime(2013, 01, 01, 10)]
LIVE_END_DATE = [datetime(2015, 01, 01, 14), datetime(2013, 01, 05, 10)]

NO_RESERVATION_PERIODS = [(datetime(2010, 01, 01, 10), LIVE_START_DATE[1]),
                          (LIVE_END_DATE[0], datetime(2016, 01, 01, 01))]
RESERVATION_PERIODS = [(LIVE_START_DATE[0], LIVE_END_DATE)]

INITIAL_DATE = datetime(1990, 01, 01, 10)
FINAL_DATE = datetime(2100, 01, 01, 10)


BLOCKING_PRINCIPALS = [
    {
        'entity_type': 'avatar',
        'entity_id': 'tim'
    }
]


BLOCKED_ROOMS = [
    {
        'state': 2,
        'rejected_by': 'tim',
        'rejection_reason': 'radioactive contamination',
        'room': 'reception'
    },

    {
        'state': 0,
        'rejected_by': None,
        'rejection_reason': None,
        'room': 'main-meeting-hall'
    }
]


BLOCKINGS = [
    {
        'created_by_id': 'admin',
        'created_dt': _create_utc_dt(2013, 11, 1, 8),
        'start_date': datetime(2013, 12, 15, 8),
        'end_date': datetime(2013, 12, 15, 17, 30),
        'reason': 'maintenance',
        'blocked_rooms': BLOCKED_ROOMS,
        'allowed': BLOCKING_PRINCIPALS
    }
]


RESERVATION_ATTRIBUTES = [
    {
        'name': 'AVC',
        'raw_data': '{"is_used": false}'
    },
    {
        'name': 'Vidyo',
        'raw_data': '{"is_used": true, "comment": "actually optional in case needed"}'
    },
    {
        'name': 'Assistance',
        'raw_data': '{"is_used": true}'
    },
    {
        'name': 'HERMES Collaboration',
        'raw_data': '{"is_used": true}'
    },
]


RESERVATION_EDIT_LOGS = [
    {
        'timestamp': _create_utc_dt(2013, 12, 2, 11, 33, 57),
        'user_name': 'johhny',
        'info': ['name updated', 'flag is cleared']
    },
    {
        'timestamp': _create_utc_dt(2013, 12, 2, 11, 34, 17),
        'user_name': 'admin',
        'info': ['removed bad words from reason', 'some value changed', 'set flag']
    }
]


RESERVATION_NOTIFICATIONS = [
    # auto generated
]

RESERVATIONS = [
    {
        'created_dt': _create_utc_dt(2013, 12, 2, 11, 30),
        'start_dt': LIVE_START_DATE[1],
        'end_dt': LIVE_END_DATE[1],
        'repeat_frequency': RepeatFrequency.MONTH,
        'repeat_interval': 1,
        'booked_for_name': 'admin',
        'is_accepted': True,
        'is_rejected': False,
        'is_cancelled': False,
        'booking_reason': 'This is what I want',
        'contact_email': 'admin@cern.ch',
        'contact_phone': '*123#',
        'attributes': RESERVATION_ATTRIBUTES,
        'edit_logs': RESERVATION_EDIT_LOGS
    },
    {
        'created_dt': _create_utc_dt(2013, 11, 2, 11, 30),
        'start_dt': LIVE_START_DATE[0],
        'end_dt': LIVE_END_DATE[0],
        'repeat_frequency': RepeatFrequency.WEEK,
        'repeat_interval': 1,
        'booked_for_name': 'admin root',
        'is_accepted': True,
        'is_rejected': False,
        'is_cancelled': False,
        'booking_reason': 'weekly group meetings',
        'contact_email': 'admin@cern.ch',
        'contact_phone': '*123#',
        'attributes': RESERVATION_ATTRIBUTES[1:3],
        'edit_logs': [],
    },
    {
        'created_dt': _create_utc_dt(2013, 11, 30, 17),
        'start_dt': LIVE_START_DATE[0],
        'end_dt': LIVE_END_DATE[0],
        'repeat_frequency': RepeatFrequency.MONTH,
        'repeat_interval': 1,
        'booked_for_name': 'admin root',
        'is_accepted': True,
        'is_rejected': False,
        'is_cancelled': False,
        'booking_reason': 'confidential',
        'contact_email': 'admin@cern.ch',
        'contact_phone': '*123#',
        'attributes': RESERVATION_ATTRIBUTES[1:3],
        'edit_logs': [],
    },
    {
        'created_dt': _create_utc_dt(2013, 12, 1, 11, 30),
        'start_dt': LIVE_START_DATE[0],
        'end_dt': LIVE_END_DATE[0],
        'repeat_frequency': RepeatFrequency.NEVER,
        'repeat_interval': 1,
        'booked_for_name': 'tim ferref',
        'is_accepted': True,
        'is_rejected': False,
        'is_cancelled': True,
        'booking_reason': 'can not be null',
        'contact_email': 'admin@cern.ch',
        'contact_phone': '*123#',
        'attributes': RESERVATION_ATTRIBUTES[3:],
        'edit_logs': [],
    },
    {
        'created_dt': _create_utc_dt(2013, 12, 20),
        'start_dt': LIVE_START_DATE[0],
        'end_dt': LIVE_END_DATE[0],
        'repeat_frequency': RepeatFrequency.NEVER,
        'repeat_interval': 1,
        'booked_for_name': 'john kusack',
        'is_accepted': False,
        'is_cancelled': False,
        'is_rejected': True,
        'booking_reason': 'extra',
        'contact_email': 'admin@cern.ch',
        'contact_phone': '*123#',
        'attributes': RESERVATION_ATTRIBUTES[3:],
        'edit_logs': [],
    },
    {
        'created_dt': _create_utc_dt(2012, 1, 1, 12),
        'start_dt': LIVE_START_DATE[0],
        'end_dt': LIVE_END_DATE[0],
        'repeat_frequency': RepeatFrequency.NEVER,
        'repeat_interval': 1,
        'booked_for_name': 'fred williams',
        'is_accepted': True,
        'is_rejected': False,
        'is_cancelled': False,
        'booking_reason': 'no reason, he just wanted me to book',
        'contact_email': 'admin@cern.ch',
        'contact_phone': '*123#',
        'attributes': RESERVATION_ATTRIBUTES,
        'edit_logs': [],
    },
    {
        'created_dt': _create_utc_dt(2008, 3, 3, 3, 3, 3),
        'start_dt': LIVE_START_DATE[0],
        'end_dt': LIVE_END_DATE[0],
        'repeat_frequency': RepeatFrequency.NEVER,
        'repeat_interval': 1,
        'booked_for_name': 'tim',
        'is_accepted': True,
        'is_rejected': False,
        'is_cancelled': False,
        'booking_reason': 'big day for me',
        'contact_email': 'admin@cern.ch',
        'contact_phone': '*123#',
        'attributes': RESERVATION_ATTRIBUTES,
        'edit_logs': [],
    },
    {
        'created_dt': _create_utc_dt(2013, 11, 11, 11, 1, 1),
        'start_dt': LIVE_START_DATE[0],
        'end_dt': LIVE_END_DATE[0],
        'repeat_frequency': RepeatFrequency.WEEK,
        'repeat_interval': 2,
        'booked_for_name': 'ferhat elmas',
        'is_accepted': False,
        'is_cancelled': False,
        'is_rejected': True,
        'booking_reason': 'testing',
        'contact_email': 'admin@cern.ch, roflcopter@cern.ch',
        'contact_phone': '*123#',
        'attributes': RESERVATION_ATTRIBUTES,
        'edit_logs': [],
    },
    {
        'created_dt': _create_utc_dt(2013, 12, 1, 23, 59),
        'start_dt': LIVE_START_DATE[0],
        'end_dt': LIVE_END_DATE[0],
        'repeat_frequency': RepeatFrequency.DAY,
        'repeat_interval': 1,
        'booked_for_name': 'ferhat elmas',
        'is_accepted': False,
        'is_rejected': False,
        'is_cancelled': False,
        'booking_reason': 'special testing',
        'contact_email': 'admin@cern.ch',
        'contact_phone': '*123#',
        'attributes': RESERVATION_ATTRIBUTES,
        'edit_logs': [],
    },
    {
        'created_dt': _create_utc_dt(2013, 12, 31, 23, 59),
        'start_dt': LIVE_START_DATE[0],
        'end_dt': LIVE_END_DATE[0],
        'repeat_frequency': RepeatFrequency.NEVER,
        'repeat_interval': 1,
        'booked_for_name': 'ferhat elmas',
        'is_accepted': True,
        'is_rejected': False,
        'is_cancelled': False,
        'booking_reason': 'special testing',
        'contact_email': 'admin@cern.ch',
        'contact_phone': '*123#',
        'attributes': [],
        'edit_logs': [],
    }
]

ROOM_ATTRIBUTE_ASSOCIATIONS = [
    {
        'attribute': 'manager-group',
        'room': 'reception',
        'value': 'fake_group'},
    {
        'attribute': 'manager-group',
        'room': 'main-meeting-hall',
        'value': 'another_group'
    },
    {
        'attribute': 'allowed-booking-group',
        'room': 'F2',
        'value': 'fake_group'
    }
]


ROOM_ATTRIBUTES = [
    {
        'name': 'manager-group',
        'title': 'Manager Group',
        'type': 'str',
        'is_required': True,
        'is_hidden': True,
    },
    {
        'name': 'map-url',
        'title': 'Map URL',
        'type': 'str',
        'is_required': True,
        'is_hidden': True,
    },
    {
        'name': 'test',
        'title': 'Test',
        'type': 'str',
        'is_required': True,
        'is_hidden': True,
    },
    {
        'name': 'allowed-booking-group',
        'title': 'Allowed Booking Group',
        'type': 'str',
        'is_required': True,
        'is_hidden': True,
    },
]


ROOM_EQUIPMENT = [
    'Blackboard',
    'Computer Projector',
    'Ethernet',
    'Telephone conference',
    'Wireless',
    'PC',
    'Video conference',
    'Telephone line',
    'Webcast/Recording',
    'Microphone',
    'Whiteboard'
]


ROOM_BOOKABLE_HOURS = [
    {
        'start_time': time(8),
        'end_time': time(18, 30)
    },
    {
        'start_time': time(19),
        'end_time': time(23, 59, 59)
    }
]

NOT_FITTING_HOURS = {'start_time': time(7),
                     'end_time': time(20, 30)}


ROOM_NONBOOKABLE_PERIODS = [
    {
        'start_dt': datetime(2013, 12, 20, 17, 30),
        'end_dt': datetime(2014, 1, 6, 8)
    },
    {
        'start_dt': datetime(2015, 12, 01),
        'end_dt': datetime(2015, 12, 02)
    }

]


PHOTOS = {
    'thumbnail': urandom(randint(0, 1024)),
    'data': urandom(randint(1025, 4096))
}

#The order of rooms is very critical when testing. If you want
#to add new rooms please do it at the end of the list.
ROOM_WITH_DUMMY_MANAGER_GROUP = 1
ROOM_WITH_DUMMY_ALLOWED_BOOKING_GROUP = 4
ROOMS = [
    {
        'name': 'main-meeting-hall',
        'site': 'meyrin',
        'division': 'IT-AVS-CIS',
        'building': '513',
        'floor': '2',
        'number': '001',
        'is_active': True,
        'is_reservable': True,
        'reservations_need_confirmation': False,
        'reservations': [],
        'capacity': 80,
        'surface_area': 145,
        'latitude': '42.45',
        'longitude': '11.09',
        'comments': u'☢ Please do not book unless really really necessary ☢',
        'max_advance_days': 45,
        'bookable_hours': ROOM_BOOKABLE_HOURS[:1],
        'nonbookable_periods': ROOM_NONBOOKABLE_PERIODS,
        'available_equipment': ROOM_EQUIPMENT[6:9],
        'photo': {},
        'attributes': ROOM_ATTRIBUTES[:2]
    },
    {
        'name': 'reception',
        'site': 'meyrin',
        'division': 'admin',
        'building': '33',
        'floor': '1',
        'number': '0',
        'capacity': 80,
        'surface_area': 145,
        'is_active': True,
        'is_reservable': True,
        'nonbookable_periods': ROOM_NONBOOKABLE_PERIODS,
        'bookable_hours': ROOM_BOOKABLE_HOURS[:1],
        'reservations': RESERVATIONS[:9],
        'photo': PHOTOS,
        'available_equipment': ROOM_EQUIPMENT[:8],
        'attributes': ROOM_ATTRIBUTES
    },
    {
        'name': 'John\'s extra office',
        'site': 'meyrin',
        'division': 'IT',
        'building': '31',
        'floor': 'R',
        'number': 'last one on the right',
        'reservations_need_confirmation': False,
        'is_active': True,
        'is_reservable': False,
        'reservations': [],
        'max_advance_days': 7,
        'photo': {},
        'bookable_hours': ROOM_BOOKABLE_HOURS[1:],
        'nonbookable_periods': ROOM_NONBOOKABLE_PERIODS,
        'available_equipment': [],
        'attributes': []
    },
    {
        'name': 'F1',
        'site': 'munchen',
        'division': 'physics',
        'building': 'center',
        'floor': '0',
        'number': '1',
        'capacity': 10,
        'surface_area': 30,
        'reservations': [],
        'photo': {},
        'is_active': False,
        'is_reservable': True,
        'available_equipment': ROOM_EQUIPMENT[5:7],
        'bookable_hours': ROOM_BOOKABLE_HOURS[:1],
        'nonbookable_periods': [],
        'attributes': []
    },
    {
        'name': 'F2',
        'building': 'right',
        'floor': '0',
        'number': '2',
        'capacity': 115,
        'surface_area': 115,
        'photo': {},
        'is_active': True,
        'is_reservable': True,
        'reservations': RESERVATIONS[9:],
        'bookable_hours': [],
        'available_equipment': [],
        'nonbookable_periods': [],
        'attributes': ROOM_ATTRIBUTES[2:]
    },
    {
        'name': 'default_room',
        'building': 'default',
        'floor': '0',
        'number': '0',
        'capacity': 20,
        'is_active': True,
        'is_reservable': True,
        'reservations_need_confirmation': False,
        'notification_before_days': 0,
        'notification_for_responsible': False,
        'notification_for_assistance': False,
        'reservations': [],
        'bookable_hours': [],
        'photo': {},
        'available_equipment': [],
        'max_advance_days': 30,
        'nonbookable_periods': [],
        'attributes': []
    }

]


ASPECTS = [
    {
        'name': 'main',
        'center_latitude': '35.42',
        'center_longitude': '38.59',
        'zoom_level': 1,
        'top_left_latitude': '32.01',
        'top_left_longitude': '23.21',
        'bottom_right_latitude': '28.27',
        'bottom_right_longitude': '40.03',
    },
    {
        'name': 'eye-view',
        'center_latitude': '35.42',
        'center_longitude': '38.59',
        'zoom_level': 4,
        'top_left_latitude': '38.01',
        'top_left_longitude': '17.21',
        'bottom_right_latitude': '22.27',
        'bottom_right_longitude': '46.03',
    }
]


LOCATIONS = [
    {
        'name': 'CERN',
        'is_default': True,
        'aspects': ASPECTS,
        'default_aspect_id': 0,
        'rooms': ROOMS[:3],
        'attributes': ROOM_ATTRIBUTES,
        'equipment_types': ROOM_EQUIPMENT
    },
    {
        'name': 'FermiLab',
        'is_default': False,
        'aspects': [],
        'rooms': ROOMS[3:],
        'default_aspect_id': 1,
        'attributes': [],
        'equipment_types': ROOM_EQUIPMENT[5:]
    },
    {
        'name': 'EmptyLocation',
        'is_default': False,
        'aspects': [],
        'rooms': [],
        'default_aspect_id': 2,
        'attributes': [],
        'equipment_types': ROOM_EQUIPMENT[5:]
    }
]
