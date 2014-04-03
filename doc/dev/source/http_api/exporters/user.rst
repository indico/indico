User
=====

General Information
-------------------

The user export is only available for authenticated users, i.e. when
using an API key and a signature (if enabled).


URL Format
----------
*/export/user/USER_ID.TYPE*

The *USER_ID* should be the user ID, e.g. *44*.


Parameters
----------

None


Results
-------------

Returns the user information (or an error in *JSON* format).

Result for https://indico.server/export/user/36024.json?ak=00000000-0000-0000-0000-000000000000&pretty=yes::

    {
        "count": 1,
        "additionalInfo": {},
        "_type": "HTTPAPIResult",
        "complete": true,
        "url": "https:\/\/indico.server\/export\/user\/36024.json?ak=00000000-0000-0000-0000-000000000000&pretty=yes",
        "ts": 1367243741,
        "results": [
            {
            "_type": "Avatar",
            "name": "Alberto RESCO PEREZ",
            "firstName": "Alberto",
            "affiliation": "CERN",
            "familyName": "Resco Perez",
            "email": "test@cern.ch",
            "phone": "+41XXXXXXXXX",
            "_fossil": "avatar",
            "title": "",
            "id": "36024"
            }
        ]
    }


