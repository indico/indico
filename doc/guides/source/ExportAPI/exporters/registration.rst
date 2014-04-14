============
Registration
============

Registrant list
===============

URL Format
----------
``/export/event/EVENT_ID/registrants.TYPE``

``TYPE`` should be ``json`` or ``xml``

Results
--------

Returns the registrant list or error information it there were any problems.

For example::

    https://indico.server/export/event/0/registrants.json?ak=00000000-0000-0000-0000-000000000000&pretty=yes&nocache=yes

Result::

    {
        "count": 1,
        "additionalInfo": {},
        "_type": "HTTPAPIResult",
        "complete": true,
        "url": "\/export\/event\/0\/registrants.json?ak=00000000-0000-0000-0000-000000000000&pretty=yes&nocache=yes",
        "ts": 1396431439,
        "results": {
            "registrants": [
                {
                    "checkin_secret": "00000000-0000-0000-0000-000000000000",
                    "checked_in": true,
                    "personal_data": {
                        "city": "Geneva",
                        "fax": "+41227000000",
                        "surname": "Resco Perez",
                        "firstName": "Alberto",
                        "title": "",
                        "country": "CH",
                        "email": "xxxxx.xxxxx.xxxxxx@cern.ch",
                        "phone": "+41227000001",
                        "personalHomepage": "",
                        "address": "",
                        "position": "",
                        "institution": "CERN"
                    },
                    "full_name": "Alberto Resco Perez",
                    "registrant_id": "0"
                }
            ]
        }
    }


Registrant
==========

URL Format
----------
``/export/event/EVENT_ID/registrant/REGISTRANT_ID.TYPE``

``TYPE`` should be ``json`` or ``xml``

Parameters
----------

==============  ================  =======================================================================
Param           Values            Description
==============  ================  =======================================================================
auth_key        text              Authentication Key in order to be able to get the registrant data
==============  ================  =======================================================================


Detail Levels
-------------

basic
~~~~~

Returns only the personal data of the registrant.

For example::

    https://indico.server/export/event/0/registrant/0.json?ak=00000000-0000-0000-0000-000000000000&detail=basic&pretty=yes&nocache=yes

Result::

    {
        "count": 10,
        "additionalInfo": {},
        "_type": "HTTPAPIResult",
        "complete": true,
        "url": "\/export\/event\/0\/registrant\/0.json?ak=00000000-0000-0000-0000-000000000000&detail=basic&pretty=yes&nocache=yes",
        "ts": 1396431698,
        "results": {
            "_type": "Registrant",
            "checked_in": true,
            "amount_paid": 0,
            "registration_date": "27\/03\/2014 12:20",
            "paid": false,
            "_fossil": "regFormRegistrantBasic",
            "personal_data": {
                "city": "Geneva",
                "fax": "+41227000000",
                "surname": "Resco Perez",
                "firstName": "Alberto",
                "title": "",
                "country": "CH",
                "email": "xxxxx.xxxxx.xxxxxx@cern.ch",
                "phone": "+41227000001",
                "personalHomepage": "",
                "address": "",
                "position": "",
                "institution": "CERN"
            },
            "full_name": "Alberto Resco Perez",
            "checkin_date": "01\/04\/2014 17:27",
            "registrant_id": "0"
        }
    }

full
~~~~

Returns the full registrant data.

For example::

    https://indico.server/export/event/0/registrant/0.json?ak=00000000-0000-0000-0000-000000000000&detail=full&pretty=yes&nocache=yes

Result::

    {
        "count": 14,
        "additionalInfo": {},
        "_type": "HTTPAPIResult",
        "complete": true,
        "url": "/export/event/301397/registrant/0.json?ak=00000000-0000-0000-0000-000000000000&detail=full&pretty=yes&nocache=yes",
        "ts": 1396436802,
        "results": {
            "_type": "Registrant",
            "checked_in": true,
            "amount_paid": 4,
            "registration_date": "24/03/2014 12:42",
            "reasonParticipation": "",
            "paid": true,
            "_fossil": "regFormRegistrantFull",
            "socialEvents": [],
            "full_name": "Alberto Resco Perez",
            "sessionList": [],
            "checkin_date":  "24/03/2014 12:45",
            "registrant_id": "0",
            "accommodation": {
                "_type": "Accommodation",
                "arrivalDate": "02-04-2014",
                "price": 0,
                "departureDate": "02-04-2014",
                "billable": false,
                "_fossil": "regFormAccommodation",
                "accommodationType": null
            },
            "miscellaneousGroupList": [
                {
                    "_fossil": "regFormMiscellaneousInfoGroupFull",
                    "_type": "MiscellaneousInfoGroup",
                    "id": "0",
                    "responseItems": [
                        {
                            "_type": "MiscellaneousInfoSimpleItem",
                            "HTMLName": "*genfield*0-11",
                            "caption": "Personal homepage",
                            "price": 0,
                            "value": "",
                            "currency": "",
                            "_fossil": "regFormMiscellaneousInfoSimpleItem",
                            "id": "11",
                            "quantity": 0
                        },
                        {
                            "_type": "MiscellaneousInfoSimpleItem",
                            "HTMLName": "*genfield*0-10",
                            "caption": "Email",
                            "price": 0,
                            "value": "alberto.resco.perez@cern.ch",
                            "currency": "",
                            "_fossil": "regFormMiscellaneousInfoSimpleItem",
                            "id": "10",
                            "quantity": 0
                        },
                        {
                            "_type": "MiscellaneousInfoSimpleItem",
                            "HTMLName": "*genfield*0-12",
                            "caption": "asdas",
                            "price": "4",
                            "value": 1,
                            "currency": "CHF",
                            "_fossil": "regFormMiscellaneousInfoSimpleItem",
                            "id": "12",
                            "quantity": 1
                        },
                        {
                            "_type": "MiscellaneousInfoSimpleItem",
                            "HTMLName": "*genfield*0-1",
                            "caption": "First Name",
                            "price": 0,
                            "value": "Alberto",
                            "currency": "",
                            "_fossil": "regFormMiscellaneousInfoSimpleItem",
                            "id": "1",
                            "quantity": 0
                        },
                        ...
                    ],
                    "title": "Personal Data"
                }
            ]
        }
    }


Set Paid
========

URL Format
----------
``/api/event/EVENT_ID/registrant/REGISTRANT_ID/pay.TYPE``

``TYPE`` should be ``json`` or ``xml``

Parameters
----------

==============  ================  =======================================================================
Param           Values            Description
==============  ================  =======================================================================
is_paid         yes, no           If specifed set (or not) as paid
==============  ================  =======================================================================

Results
--------

**POST request**

Returns the status of the payment and the paid amount.

For example::

    curl --data "ak=00000000-0000-0000-0000-000000000000&is_paid=yes" 'https://indico.server/api/event/0/registrant/pay.json'

Result::

    {
        "count": 2,
        "additionalInfo": {},
        "_type": "HTTPAPIResult",
        "complete": true,
        "url": "\/api\/event\/301397\/registrant\/0\/pay.json?ak=00000000-0000-0000-0000-000000000000&is_paid=yes",
        "ts": 1396431439,
        "results": {
            "paid": true,
            "amount_paid": 4.0
        }
    }


Check-in
========

URL Format
----------
``/api/event/EVENT_ID/registrant/REGISTRANT_ID/checkin.TYPE``

``TYPE`` should be ``json`` or ``xml``

Parameters
----------

==============  ================  =======================================================================
Param           Values            Description
==============  ================  =======================================================================
secret          text              Secret key that gets generated along with the ticket (QR Code)
checked_in      yes, no           If specifed set (or not) as checked in
==============  ================  =======================================================================

Results
--------

**POST request**

Returns the status of the check-in and the check-in date

For example::

    curl --data "ak=00000000-0000-0000-0000-000000000000&secret=00000000-0000-0000-0000-000000000000&checked_in=yes" 'https://indico.server/api/event/0/registrant/checkin.json'

Result::

    {
        "count": 2,
        "additionalInfo": {},
        "_type": "HTTPAPIResult",
        "complete": true,
        "url": "\/api\/event\/301397\/registrant\/0\/pay.json?ak=00000000-0000-0000-0000-000000000000&secret=00000000-0000-0000-0000-000000000000&checked_in=yes",
        "ts": 1396431439,
        "results": {
            "checked_in": true,
            "checkin_date":  "24/03/2014 12:45",
        }
    }
