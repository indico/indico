============
Room Booking
============

Bookings
========


Creating bookings
*****************

General Information
-------------------

The Room Booking API is only available for authenticated users,
i.e. when using an API key and a signature (if enabled).
If the room booking system is restricted to certain users/groups this
restriction applies for this API, too.
The request will fail if there is a collision with another booking, blocking or unavailable period.

Note that it is not possible to pre-book a room through this api.

URL Format
----------
*/api/roomBooking/bookRoom.TYPE*

*TYPE* should be *json* or *xml*.


Parameters
----------

The following parameters are required:

==============  ================  =======================================================================
Param           Values            Description
==============  ================  =======================================================================
location        text              Room location, e.g. *CERN*
roomid          text              Room id
from/to         f/t               Start/End time for a booking. Accepted formats:
                                        * ISO 8601 subset - YYYY-MM-DD[THH:MM]
                                        * 'today', 'yesterday', 'tomorrow' and 'now'
                                        * days in the future/past: '[+/-]DdHHhMMm'
reason          text              Reason for booking a room
username        text              User login name for whom the booking will be created
==============  ================  =======================================================================


Booking a room
~~~~~~~~~~~~~~

 **POST request**

Returns *reservation id* if the booking was successful or error information it there were any problems.

For example::

    curl --data "username=jdoe&from=2012-12-30T21:30&to=2012-12-30T22:15&reason=meeting&location=CERN&roomid=189" 'http://indico.server/indico/api/roomBooking/bookRoom.json'

Result::

    {
        {
            "url": "\/api\/roomBooking\/bookRoom.json",
            "_type": "HTTPAPIResult",
            "results": {
                "reservationID": 45937
            },
            "ts": 1354695663
        }
    }


Retrieving bookings
*******************

General Information
-------------------

The reservation export is only availabled for authenticated users,
i.e. when using an API key and a signature (if enabled).
If the room booking system is restricted to certain users/groups this
restriction applies for the reservation export API, too.

Please note that the room export with the *reservations* detail level
is much more appropriate if you need reservations for specific rooms.


URL Format
----------
*/export/reservation/LOCATION.TYPE*

The *LOCATION* should be the room location, e.g. *CERN*. A *-* separated
list of multiple locations is allowed, too.


Parameters
----------

.. include:: _rb_params.rst


Detail Levels
-------------

reservations
~~~~~~~~~~~~

Returns detailed data about the reservations and the most important
information about the booked room.

For example, https://indico.server/export/reservation/CERN.json?ak=00000000-0000-0000-0000-000000000000&detail=reservations&from=today&to=today&bookedfor=*MONNICH*&pretty=yes::

    {
        "count": 1,
        "_type": "HTTPAPIResult",
        "complete": true,
        "url": "https://indico.server/export/reservation/CERN.json?ak=00000000-0000-0000-0000-000000000000&detail=reservations&from=today&to=today&bookedfor=*MONNICH*&pretty=yes",
        "ts": 1308923111,
        "results": [
            {
                "endDT": {
                    "date": "2011-06-25",
                    "tz": "Europe/Zurich",
                    "time": "17:30:00"
                },
                "room": {
                    "_fossil": "minimalRoomMetadata",
                    "_type": "RoomCERN",
                    "fullName": "500-1-201 - Mezzanine",
                    "id": 120
                },
                "isConfirmed": true,
                "isValid": true,
                "usesAVC": false,
                "repeatability": "daily",
                "_type": "ReservationCERN",
                "vcList": [],
                "reason": "Just testing",
                "location": "CERN",
                "_fossil": "reservationMetadata",
                "needsAVCSupport": false,
                "startDT": {
                    "date": "2011-06-24",
                    "tz": "Europe/Zurich",
                    "time": "08:30:00"
                },
                "id": 93094,
                "bookingUrl": "http://indico.server/roomBooking.py/bookingDetails?roomLocation=CERN&resvID=93094",
                "bookedForName": "MONNICH, Jerome"
            }
        ]
    }



Rooms
=====

General Information


The room export is only availabled for authenticated users, i.e. when
using an API key and a signature (if enabled).
If the room booking system is restricted to certain users/groups this
restriction applies for the room export API, too.


URL Format
**********
*/export/room/LOCATION/ID.TYPE*

The *LOCATION* should be the room location, e.g. *CERN*.
The *ID* can be either a single room ID or a *-* separated list.


Parameters
**********

.. include:: _rb_params.rst


Detail Levels
*************

rooms
-----

Returns basic data about the rooms.

For example, https://indico.server/export/room/CERN/120.json?ak=00000000-0000-0000-0000-000000000000&pretty=yes::

    {
        "count": 1,
        "_type": "HTTPAPIResult",
        "complete": true,
        "url": "https://indico.server/export/room/CERN/120.json?ak=00000000-0000-0000-0000-000000000000&pretty=yes",
        "ts": 1308921960,
        "results": [
            {
                "building": 500,
                "_type": "RoomCERN",
                "name": "Mezzanine",
                "floor": "1",
                "longitude": "6.05427049127",
                "vcList": [],
                "equipment": [],
                "roomNr": "201",
                "location": "CERN",
                "_fossil": "roomMetadata",
                "latitude": "46.2314139466",
                "fullName": "500-1-201 - Mezzanine",
                "id": 120,
                "bookingUrl": "http://indico.server/roomBooking.py/bookingForm?roomLocation=CERN&roomID=120",
                "avc": false
            }
        ]
    }


reservations
------------

Returns basic data about the rooms and their reservations in the given timeframe.

Output for https://indico.server/export/room/CERN/120.json?ak=00000000-0000-0000-0000-000000000000&detail=reservations&from=today&to=today&pretty=yes::

    {
        "count": 1,
        "_type": "HTTPAPIResult",
        "complete": true,
        "url": "https://indico.server/export/room/CERN/120.json?ak=00000000-0000-0000-0000-000000000000&detail=reservations&from=today&to=today&pretty=yes",
        "ts": 1308922107,
        "results": [
            {
                "building": 500,
                "_type": "RoomCERN",
                "name": "Mezzanine",
                "floor": "1",
                "longitude": "6.05427049127",
                "reservations": [
                    {
                        "endDT": {
                            "date": "2011-06-25",
                            "tz": "Europe/Zurich",
                            "time": "17:30:00"
                        },
                        "isConfirmed": true,
                        "isValid": true,
                        "usesAVC": false,
                        "repeatability": "daily",
                        "_type": "ReservationCERN",
                        "vcList": [],
                        "reason": "Just testing",
                        "bookedForName": "MONNICH, Jerome",
                        "_fossil": "roomReservationMetadata",
                        "needsAVCSupport": false,
                        "startDT": {
                            "date": "2011-06-24",
                            "tz": "Europe/Zurich",
                            "time": "08:30:00"
                        },
                        "id": 93094,
                        "bookingUrl": "http://indico.server/roomBooking.py/bookingDetails?roomLocation=CERN&resvID=93094"
                    }
                ],
                "vcList": [],
                "equipment": [],
                "roomNr": "201",
                "location": "CERN",
                "_fossil": "roomMetadataWithReservations",
                "latitude": "46.2314139466",
                "fullName": "500-1-201 - Mezzanine",
                "id": 120,
                "bookingUrl": "http://indico.server/roomBooking.py/bookingForm?roomLocation=CERN&roomID=120",
                "avc": false
            }
        ]
    }

Get room by room name
=====================

General Information

The search room export is guest allowed because the room data is public (no the reservations).


URL Format
**********
*/export/roomName/LOCATION/ROOMNAME.TYPE*

The *LOCATION* should be the room location, e.g. *CERN*.
The *ROOMNAME* is a single ROOMNAME.


Parameters
**********

No parameters needed.


Results
*************

Returns basic data about the rooms.

For example, https://indico.server/export/roomName/CERN/Mezzanine.json?ak=00000000-0000-0000-0000-000000000000&pretty=yes::

    {
        "count": 1,
        "_type": "HTTPAPIResult",
        "complete": true,
        "url": "https://indico.server/export/room/CERN/120.json?ak=00000000-0000-0000-0000-000000000000&pretty=yes",
        "ts": 1308921960,
        "results": [
            {
                "building": 500,
                "_type": "RoomCERN",
                "name": "Mezzanine",
                "floor": "1",
                "longitude": "6.05427049127",
                "vcList": [],
                "equipment": [],
                "roomNr": "201",
                "location": "CERN",
                "_fossil": "roomMetadata",
                "latitude": "46.2314139466",
                "fullName": "500-1-201 - Mezzanine",
                "id": 120,
                "bookingUrl": "http://indico.server/roomBooking.py/bookingForm?roomLocation=CERN&roomID=120",
                "avc": false
            }
        ]
    }

