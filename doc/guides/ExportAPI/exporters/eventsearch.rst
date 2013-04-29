Event Search
===============

URL Format
----------
*/export/event/search/TERM.TYPE*

The TERM should be an string, e.g. "ichep"


Results
-------------

Returns the events found.

Result for https://indico.server/export/event/search/ichep.json?ak=00000000-0000-0000-0000-000000000000&pretty=yes::

    {
        "count": 5,
        "additionalInfo": {},
        "_type": "HTTPAPIResult",
        "complete": true,
        "url": "https:\/\/indico.server\/export\/event\/search\/ichep.json?ak=00000000-0000-0000-0000-000000000000&pretty=yes",
        "ts": 1367245058,
        "results": [
            {
                "startDate": {
                    "date": "2010-07-16",
                    "tz": "UTC",
                    "time": "11:00:00"
                },
                "hasAnyProtection": false,
                "id": "101465",
                "title": "Rehearsals for ICHEP Friday 16th July Afternoon Session"
            },
            {
                "startDate": {
                    "date": "2010-08-06",
                    "tz": "UTC",
                    "time": "12:00:00"
                },
                "hasAnyProtection": false,
                "id": "102669",
                "title": "Overview of LHC physics results at ICHEP"
            },
            {
                "startDate": {
                    "date": "2010-08-18",
                    "tz": "UTC",
                    "time": "17:00:00"
                },
                "hasAnyProtection": false,
                "id": "104128",
                "title": "Seminer Oturumu: \"ATLAS status and highlights as of ICHEP\" Dr. Tayfun Ince (Universitaet Bonn)"
            },
            {
                "startDate": {
                    "date": "2011-07-23",
                    "tz": "UTC",
                    "time": "11:00:00"
                },
                "hasAnyProtection": false,
                "id": "145521",
                "title": "89th Plenary ECFA and Joint EPS\/ICHEP-ECFA Session - Grenoble, France"
            },
            {
                "startDate": {
                    "date": "2012-01-12",
                    "tz": "UTC",
                    "time": "08:00:00"
                },
                "hasAnyProtection": false,
                "id": "168897",
                "title": "ICHEP 2012 Outreach Planning Meeting"
            }
        ]
    }

