Events
===============

URL Format
----------
*/export/event/ID.TYPE*

The ID can be either a single event ID or a *-* separated list.


Parameters
----------

===========  =====  =======================================================
Param        Short  Description
===========  =====  =======================================================
occurrences  occ    Include the daily event times in the exported data.
===========  =====  =======================================================


Detail Levels
-------------

events
~~~~~~
Returns basic data about the event. In this example occurrences are
included, too.

Result for https://indico.server/export/event/137346.json?occ=yes&pretty=yes::

    {
        "count": 1,
        "_type": "HTTPAPIResult",
        "complete": true,
        "url": "https://indico.server/export/event/137346.json?occ=yes&pretty=yes",
        "ts": 1308899256,
        "results": [
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
                "url": "http://indico.server/conferenceDisplay.py?confId=137346",
                "room": null,
                "occurrences": [
                    {
                        "_fossil": "period",
                        "endDT": {
                            "date": "2011-06-23",
                            "tz": "Europe/Zurich",
                            "time": "08:40:00"
                        },
                        "startDT": {
                            "date": "2011-06-23",
                            "tz": "Europe/Zurich",
                            "time": "08:00:00"
                        },
                        "_type": "Period"
                    },
                    {
                        "_fossil": "period",
                        "endDT": {
                            "date": "2011-06-24",
                            "tz": "Europe/Zurich",
                            "time": "15:00:00"
                        },
                        "startDT": {
                            "date": "2011-06-24",
                            "tz": "Europe/Zurich",
                            "time": "12:00:00"
                        },
                        "_type": "Period"
                    }
                ],
                "_fossil": "conferenceMetadata",
                "timezone": "Europe/Zurich",
                "type": "meeting",
                "id": "137346",
                "location": "CERN"
            }
        ]
    }


contributions
~~~~~~~~~~~~~
Includes the contributions of the event.

Output for https://indico.server/export/event/137346.json?detail=contributions&pretty=yes::

    {
        "count": 1,
        "_type": "HTTPAPIResult",
        "complete": true,
        "url": "https://indico.server/export/event/137346.json?detail=contributions&pretty=yes",
        "ts": 1308899252,
        "results": [
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
                "url": "http://indico.server/conferenceDisplay.py?confId=137346",
                "type": "meeting",
                "location": "CERN",
                "_fossil": "conferenceMetadataWithContribs",
                "timezone": "Europe/Zurich",
                "contributions": [
                    {
                        "startDate": {
                            "date": "2011-06-23",
                            "tz": "Europe/Zurich",
                            "time": "08:20:00"
                        },
                        "_type": "Contribution",
                        "endDate": {
                            "date": "2011-06-23",
                            "tz": "Europe/Zurich",
                            "time": "08:40:00"
                        },
                        "description": "",
                        "title": "d1c2",
                        "track": null,
                        "duration": 20,
                        "session": null,
                        "location": "CERN",
                        "_fossil": "contributionMetadata",
                        "type": null,
                        "id": "1",
                        "room": null
                    },
                    {
                        "startDate": {
                            "date": "2011-06-23",
                            "tz": "Europe/Zurich",
                            "time": "08:00:00"
                        },
                        "_type": "Contribution",
                        "endDate": {
                            "date": "2011-06-23",
                            "tz": "Europe/Zurich",
                            "time": "08:20:00"
                        },
                        "description": "",
                        "title": "d1c1",
                        "track": null,
                        "duration": 20,
                        "session": null,
                        "location": "CERN",
                        "_fossil": "contributionMetadata",
                        "type": null,
                        "id": "0",
                        "room": null
                    },
                    {
                        "startDate": {
                            "date": "2011-06-24",
                            "tz": "Europe/Zurich",
                            "time": "14:00:00"
                        },
                        "_type": "Contribution",
                        "endDate": {
                            "date": "2011-06-24",
                            "tz": "Europe/Zurich",
                            "time": "14:20:00"
                        },
                        "description": "",
                        "title": "d2s1c1",
                        "track": null,
                        "duration": 20,
                        "session": "d2s1",
                        "location": "CERN",
                        "_fossil": "contributionMetadata",
                        "type": null,
                        "id": "3",
                        "room": null
                    },
                    {
                        "startDate": {
                            "date": "2011-06-24",
                            "tz": "Europe/Zurich",
                            "time": "12:00:00"
                        },
                        "_type": "Contribution",
                        "endDate": {
                            "date": "2011-06-24",
                            "tz": "Europe/Zurich",
                            "time": "14:00:00"
                        },
                        "description": "",
                        "title": "d2c1",
                        "track": null,
                        "duration": 120,
                        "session": null,
                        "location": "CERN",
                        "_fossil": "contributionMetadata",
                        "type": null,
                        "id": "2",
                        "room": null
                    }
                ],
                "id": "137346",
                "room": null
            }
        ]
    }


subcontributions
~~~~~~~~~~~~~~~~
Like `contributions <#contributions>`_, but inside the contributions the subcontributions
are included in a field named *subContributions*.


sessions
~~~~~~~~
Includes details about the different sessions and groups contributions by
sessions. The top-level *contributions* list only contains contributions
which are not assigned to any session. Subcontributions are included in
this details level, too.

For example, https://indico.server/export/event/137346.json?detail=sessions&pretty=yes::

    {
        "count": 1,
        "_type": "HTTPAPIResult",
        "complete": true,
        "url": "https://indico.server/export/event/137346.json?detail=sessions&pretty=yes",
        "ts": 1308899771,
        "results": [
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
                "url": "http://indico.server/conferenceDisplay.py?confId=137346",
                "contributions": [
                    {
                        "startDate": {
                            "date": "2011-06-23",
                            "tz": "Europe/Zurich",
                            "time": "08:20:00"
                        },
                        "_type": "Contribution",
                        "endDate": {
                            "date": "2011-06-23",
                            "tz": "Europe/Zurich",
                            "time": "08:40:00"
                        },
                        "description": "",
                        "subContributions": [],
                        "title": "d1c2",
                        "track": null,
                        "duration": 20,
                        "session": null,
                        "location": "CERN",
                        "_fossil": "contributionMetadataWithSubContribs",
                        "type": null,
                        "id": "1",
                        "room": null
                    },
                    {
                        "startDate": {
                            "date": "2011-06-23",
                            "tz": "Europe/Zurich",
                            "time": "08:00:00"
                        },
                        "_type": "Contribution",
                        "endDate": {
                            "date": "2011-06-23",
                            "tz": "Europe/Zurich",
                            "time": "08:20:00"
                        },
                        "description": "",
                        "subContributions": [],
                        "title": "d1c1",
                        "track": null,
                        "duration": 20,
                        "session": null,
                        "location": "CERN",
                        "_fossil": "contributionMetadataWithSubContribs",
                        "type": null,
                        "id": "0",
                        "room": null
                    },
                    {
                        "startDate": {
                            "date": "2011-06-24",
                            "tz": "Europe/Zurich",
                            "time": "12:00:00"
                        },
                        "_type": "Contribution",
                        "endDate": {
                            "date": "2011-06-24",
                            "tz": "Europe/Zurich",
                            "time": "14:00:00"
                        },
                        "description": "",
                        "subContributions": [],
                        "title": "d2c1",
                        "track": null,
                        "duration": 120,
                        "session": null,
                        "location": "CERN",
                        "_fossil": "contributionMetadataWithSubContribs",
                        "type": null,
                        "id": "2",
                        "room": null
                    }
                ],
                "sessions": [
                    {
                        "startDate": {
                            "date": "2011-06-24",
                            "tz": "Europe/Zurich",
                            "time": "14:00:00"
                        },
                        "_type": "Session",
                        "room": "",
                        "numSlots": 1,
                        "color": "#EEE0EF",
                        "material": [],
                        "isPoster": false,
                        "sessionConveners": [],
                        "location": "CERN",
                        "address": "",
                        "_fossil": "sessionMetadata",
                        "title": "d2s1",
                        "textColor": "#1D041F",
                        "contributions": [
                            {
                                "startDate": {
                                    "date": "2011-06-24",
                                    "tz": "Europe/Zurich",
                                    "time": "14:00:00"
                                },
                                "_type": "Contribution",
                                "endDate": {
                                    "date": "2011-06-24",
                                    "tz": "Europe/Zurich",
                                    "time": "14:20:00"
                                },
                                "description": "",
                                "subContributions": [],
                                "title": "d2s1c1",
                                "track": null,
                                "duration": 20,
                                "session": "d2s1",
                                "location": "CERN",
                                "_fossil": "contributionMetadataWithSubContribs",
                                "type": null,
                                "id": "3",
                                "room": null
                            }
                        ],
                        "id": "0"
                    }
                ],
                "location": "CERN",
                "_fossil": "conferenceMetadataWithSessions",
                "timezone": "Europe/Zurich",
                "type": "meeting",
                "id": "137346",
                "room": null
            }
        ]
    }

