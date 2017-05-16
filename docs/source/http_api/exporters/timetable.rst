Timetable
===============

URL Format
----------
*/export/timetable/ID.TYPE*

The ID should be the event ID, e.g. *123*.


Results
-------------

Returns the timetable of the event.

Result for https://indico.server/export/timetable/137346.json?ak=00000000-0000-0000-0000-000000000000&pretty=yes::

    {
        "count": 1,
        "additionalInfo": {},
        "_type": "HTTPAPIResult",
        "complete": true,
        "url": "https:\/\/indico.server\/export\/timetable\/137346.json?ak=00000000-0000-0000-0000-000000000000&pretty=yes",
        "ts": 1367242732,
        "results": {
            "137346": {
                "20130429": {
                    "c0": {
                        "startDate": {
                            "date": "2013-04-29",
                            "tz": "Europe\/Zurich",
                            "time": "16:00:00"
                        },
                        "_type": "ContribSchEntry",
                        "material": [],
                        "endDate": {
                            "date": "2013-04-29",
                            "tz": "Europe\/Zurich",
                            "time": "16:30:00"
                        },
                        "description": "",
                        "title": "Contrib 1",
                        "id": "c0",
                        "contributionId": "0",
                        "sessionSlotId": null,
                        "conferenceId": "137346",
                        "presenters": [],
                        "sessionId": null,
                        "location": "CERN",
                        "uniqueId": "a137346t0",
                        "_fossil": "contribSchEntryDisplay",
                        "sessionCode": null,
                        "entryType": "Contribution",
                        "room": "160-1-009"
                    }
                }
            }

