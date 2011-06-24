Reservations
============

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
information about the booked room::

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

