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

For example, https://indico.server/export/reservation/CERN.json?ak=00000000-0000-0000-0000-000000000000&detail=reservation&from=today&to=today&pretty=yes::

    {
        "count": 1,
        "additionalInfo": {},
        "_type": "HTTPAPIResult",
        "url": "/export/reservation/CERN.json?ak=00000000-0000-0000-0000-000000000000&detail=reservation&from=today&to=today&pretty=yes",
        "results": [
            {
                "_type": "Reservation",
                "repeat_unit": 1,
                "endDT": {
                    "date": "2014-08-14",
                    "tz": "Europe/Zurich",
                    "time": "12:30:00"
                },
                "room": {
                    "_type": "Room",
                    "fullName": "500-1-001 - Main Auditorium",
                    "id": 57
                },
                "needs_general_assistance": false,
                "isConfirmed": true,
                "isValid": true,
                "usesAVC": false,
                "repeatability": "daily",
                "repeat_step": 1,
                "vcList": [],
                "reason": "Summer Student Lecture programme",
                "bookedForName": "DOE, John",
                "is_rejected": false,
                "is_cancelled": false,
                "needsAVCSupport": false,
                "startDT": {
                    "date": "2014-07-02",
                    "tz": "Europe/Zurich",
                    "time": "08:30:00"
                },
                "id": 63779,
                "bookingUrl": "http://indico.server/rooms/booking/CERN/63779/",
                "location": "CERN"
            }
        ],
        "ts": 1406727843
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

For example, https://indico.server/export/room/CERN/57.json?ak=00000000-0000-0000-0000-000000000000&pretty=yes::

    {
        "count": 1,
        "additionalInfo": {},
        "_type": "HTTPAPIResult",
        "url": "/export/room/CERN/57.json?ak=00000000-0000-0000-0000-000000000000&pretty=yes",
        "results": [
            {
                "building": "500",
                "_type": "Room",
                "name": "Main Auditorium",
                "floor": "1",
                "longitude": "6.0542704900999995",
                "vcList": [
                    "Audio Conference",
                    "Built-in (MCU) Bridge",
                    "CERN MCU",
                    "ESnet MCU",
                    "EVO",
                    "H323 point2point",
                    "Vidyo"
                ],
                "equipment": [
                    "Blackboard",
                    "Computer Projector",
                    "Ethernet",
                    "Microphone",
                    "PC",
                    "Telephone conference",
                    "Video conference",
                    "Webcast/Recording",
                    "Wireless"
                ],
                "roomNr": "001",
                "location": "CERN",
                "latitude": "46.23141394580001",
                "fullName": "500-1-001 - Main Auditorium",
                "id": 57,
                "bookingUrl": "/indico/rooms/room/CERN/57/book",
                "avc": true
            }
        ],
        "ts": 1406729635
    }


reservations
------------

Returns basic data about the rooms and their reservations in the given timeframe.

Output for https://indico.server/export/room/CERN/57.json?ak=00000000-0000-0000-0000-000000000000&detail=reservations&from=today&to=today&pretty=yes::

    {
        "count": 1,
        "additionalInfo": {},
        "_type": "HTTPAPIResult",
        "url": "/export/room/CERN/57.json?ak=00000000-0000-0000-0000-000000000000&detail=reservations&from=today&to=today&pretty=yes",
        "results": [
            {
                "building": "500",
                "_type": "Room",
                "name": "Main Auditorium",
                "floor": "1",
                "reservations": [
                    {
                        "_type": "Reservation",
                        "repeat_unit": 1,
                        "endDT": {
                            "date": "2014-08-14",
                            "tz": "Europe/Zurich",
                            "time": "12:30:00"
                        },
                        "needs_general_assistance": false,
                        "isConfirmed": true,
                        "isValid": true,
                        "usesAVC": false,
                        "repeatability": "daily",
                        "repeat_step": 1,
                        "vcList": [],
                        "reason": "Summer Student Lecture programme",
                        "bookedForName": "DOE, John",
                        "is_rejected": false,
                        "is_cancelled": false,
                        "needsAVCSupport": false,
                        "startDT": {
                            "date": "2014-07-02",
                            "tz": "Europe/Zurich",
                            "time": "08:30:00"
                        },
                        "id": 63779,
                        "bookingUrl": "http://pcavc005.cern.ch:8000/indico/rooms/booking/CERN/63779/",
                        "location": "CERN"
                    }
                ],
                "longitude": "6.0542704900999995",
                "vcList": [
                    "Audio Conference",
                    "Built-in (MCU) Bridge",
                    "CERN MCU",
                    "ESnet MCU",
                    "EVO",
                    "H323 point2point",
                    "Vidyo"
                ],
                "equipment": [
                    "Blackboard",
                    "Computer Projector",
                    "Ethernet",
                    "Microphone",
                    "PC",
                    "Telephone conference",
                    "Video conference",
                    "Webcast/Recording",
                    "Wireless"
                ],
                "roomNr": "001",
                "location": "CERN",
                "latitude": "46.23141394580001",
                "fullName": "500-1-001 - Main Auditorium",
                "id": 57,
                "bookingUrl": "/indico/rooms/room/CERN/57/book",
                "avc": true
            }
        ],
        "ts": 1406731966
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

For example, https://indico.server/export/roomName/CERN/Main Auditorium.json?ak=00000000-0000-0000-0000-000000000000&pretty=yes::

    {
        "count": 1,
        "additionalInfo": {},
        "_type": "HTTPAPIResult",
        "url": "/export/roomName/CERN/Main Auditorium.json?ak=00000000-0000-0000-0000-000000000000&pretty=yes",
        "results": [
            {
                "building": "500",
                "_type": "Room",
                "name": "Main Auditorium",
                "floor": "1",
                "longitude": "6.0542704900999995",
                "vcList": [
                    "Audio Conference",
                    "Built-in (MCU) Bridge",
                    "CERN MCU",
                    "ESnet MCU",
                    "EVO",
                    "H323 point2point",
                    "Vidyo"
                ],
                "equipment": [
                    "Blackboard",
                    "Computer Projector",
                    "Ethernet",
                    "Microphone",
                    "PC",
                    "Telephone conference",
                    "Video conference",
                    "Webcast/Recording",
                    "Wireless"
                ],
                "roomNr": "001",
                "location": "CERN",
                "latitude": "46.23141394580001",
                "fullName": "500-1-001 - Main Auditorium",
                "id": 57,
                "bookingUrl": "/indico/rooms/room/CERN/57/book",
                "avc": true
            }
        ],
        "ts": 1406732578
    }

