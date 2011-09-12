Rooms
=====

General Information
-------------------

The room export is only availabled for authenticated users, i.e. when
using an API key and a signature (if enabled).
If the room booking system is restricted to certain users/groups this
restriction applies for the room export API, too.


URL Format
----------
*/export/room/LOCATION/ID.TYPE*

The *LOCATION* should be the room location, e.g. *CERN*.
The *ID* can be either a single room ID or a *-* separated list.


Parameters
----------

.. include:: _rb_params.rst


Detail Levels
-------------

rooms
~~~~~

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
                "vcList": [],
                "equipment": [],
                "roomNr": "201",
                "location": "CERN",
                "_fossil": "roomMetadata",
                "fullName": "500-1-201 - Mezzanine",
                "id": 120,
                "bookingUrl": "http://indico.server/roomBooking.py/bookingForm?roomLocation=CERN&roomID=120",
                "avc": false
            }
        ]
    }


reservations
~~~~~~~~~~~~

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
                "fullName": "500-1-201 - Mezzanine",
                "id": 120,
                "bookingUrl": "http://indico.server/roomBooking.py/bookingForm?roomLocation=CERN&roomID=120",
                "avc": false
            }
        ]
    }

