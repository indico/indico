# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
import pytz

from indico.modules.rb.api import ReservationHook, RoomHook, RoomNameHook
from indico.web.http_api import HTTPAPIHook


@pytest.mark.parametrize(('path', 'hook_cls', 'path_params'), (
    ('/export/room/CERN/23.json', RoomHook, {'location': 'CERN', 'idlist': '23'}),
    ('/export/room/HIM-Building 1395/8-9.json', RoomHook, {'location': 'HIM-Building 1395', 'idlist': '8-9'}),
    ('/export/roomName/CERN/pump.json', RoomNameHook, {'location': 'CERN', 'room_name': 'pump'}),
    ('/export/roomName/HIM-Building 1395/1/2-3.json', RoomNameHook,
     {'location': 'HIM-Building 1395', 'room_name': '1/2-3'}),
    ('/export/reservation/CERN-HIM.json', ReservationHook, {'loclist': 'CERN-HIM'}),
))
def test_parse_request_path(path, hook_cls, path_params):
    hook, format_ = HTTPAPIHook.parseRequest(path, {})
    assert isinstance(hook, hook_cls)
    assert hook._pathParams == path_params
    assert format_ == 'json'


def test_serialize_room_api(dummy_room):
    from indico.modules.rb.schemas import RoomLegacyAPISchema
    assert RoomLegacyAPISchema().dump(dummy_room) == {
        'building': '1',
        'floor': '2',
        'fullName': '1/2-3',
        'id': dummy_room.id,
        'latitude': None,
        'location': 'Test',
        'longitude': None,
        'name': '1/2-3',
        'roomNr': '3',
    }


def test_serialize_room_api_minimal(dummy_room):
    from indico.modules.rb.schemas import RoomLegacyMinimalAPISchema
    assert RoomLegacyMinimalAPISchema().dump(dummy_room) == {
        'fullName': '1/2-3',
        'id': dummy_room.id,
    }


def test_serialize_reservation(dummy_reservation):
    from indico.modules.rb.schemas import ReservationLegacyAPISchema
    assert ReservationLegacyAPISchema().dump(dummy_reservation) == {
        'bookedForName': 'Guinea Pig',
        'booked_for_user_email': '1337@example.test',
        'bookingUrl': 'http://localhost/rooms/booking/420',
        'endDT': dummy_reservation.end_dt.replace(tzinfo=pytz.utc),
        'id': dummy_reservation.id,
        'isConfirmed': True,
        'isValid': True,
        'is_cancelled': False,
        'is_rejected': False,
        'location': 'Test',
        'reason': 'Testing',
        'repeat_frequency': 'NEVER',
        'repeat_interval': 0,
        'startDT': dummy_reservation.start_dt.replace(tzinfo=pytz.utc),
    }


def test_serialize_reservation_occurrence(dummy_reservation):
    from indico.modules.rb.schemas import ReservationOccurrenceLegacyAPISchema
    assert ReservationOccurrenceLegacyAPISchema().dump(dummy_reservation.occurrences[0]) == {
        'endDT': dummy_reservation.occurrences[0].end_dt.replace(tzinfo=pytz.utc),
        'startDT': dummy_reservation.occurrences[0].start_dt.replace(tzinfo=pytz.utc),
        'is_cancelled': False,
        'is_rejected': False,
    }
