Categories
===============

URL Format
----------
*/export/categ/ID.TYPE*

The ID can be either a single category ID or a *-* separated list.
In an authenticated request the special ID *favorites* will be resolved to the user's list of favorites.


Parameters
----------

========  =====  ==========================================================
Param     Short  Description
========  =====  ==========================================================
location  l      Only include events taking place at the specified location.
                 The `*` and `?` wildcards may be used.
room      r      Only include events taking place in the specified room.
                 The `*` and `?` wildcards may be used.
type      T      Only include events of the specified type. Must be one of:
                 simple_event (or lecture), meeting, conference
========  =====  ==========================================================


Detail Levels
-------------

events
~~~~~~

Returns basic data about the events in the category.

This is the result of the following the query https://my.indico/export/categ/2.json?from=today&to=today&pretty=yes::

    {
        "count": 2,
        "_type": "HTTPAPIResult",
        "complete": true,
        "url": "https://my.indico/export/categ/2.json?from=today&to=today&pretty=yes",
        "ts": 1308841641,
        "results": [
            {
                "category": "TEST Category",
                "startDate": {
                    "date": "2011-06-17",
                    "tz": "Europe/Zurich",
                    "time": "08:00:00"
                },
                "_type": "Conference",
                "endDate": {
                    "date": "2011-06-30",
                    "tz": "Europe/Zurich",
                    "time": "18:00:00"
                },
                "description": "",
                "title": "Test EPayment",
                "url": "http://pcituds07.cern.ch/indico/conferenceDisplay.py?confId=137344",
                "location": "CERN",
                "_fossil": "conferenceMetadata",
                "timezone": "Europe/Zurich",
                "type": "conference",
                "id": "137344",
                "room": "1-1-025"
            },
            {
                "category": "TEST Category",
                "startDate": {
                    "date": "2011-06-23",
                    "tz": "Europe/Zurich",
                    "time": "08:00:00"
                },
                "_type": "Conference",
                "endDate": {
                    "date": "2011-06-24",
                    "tz": "Europe/Zurich",
                    "time": "18:00:00"
                },
                "description": "",
                "title": "Export Test",
                "url": "http://pcituds07.cern.ch/indico/conferenceDisplay.py?confId=137346",
                "location": "CERN",
                "_fossil": "conferenceMetadata",
                "timezone": "Europe/Zurich",
                "type": "meeting",
                "id": "137346",
                "room": null
            }
        ]
    }
