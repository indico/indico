# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytz


pytest_plugins = 'indico.modules.rb.testing.fixtures'


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
        'booked_for_user_email': '1337@example.com',
        'bookingUrl': 'http://localhost/rooms/booking/1',
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
