User
=====

General Information
-------------------

The user export is only available for authenticated users, i.e. when
using an API key and a signature (if enabled).

.. deprecated:: 3.3.8
    Will be removed in Indico v3.4. Use ``/api/user/`` instead.

URL Format
----------
*/export/user/USER_ID.TYPE*

The *USER_ID* should be the user ID, e.g. *44*.


Parameters
----------

None


Results
-------

Returns the user information (or an error in *JSON* format).

Result for https://indico.server/export/user/6.json?ak=00000000-0000-0000-0000-000000000000&pretty=yes::

    {
        "count": 1,
        "additionalInfo": {},
        "_type": "HTTPAPIResult"
        "ts": 1610536660,
        "url": "https:\/\/indico.server\/export\/user\/6.json?ak=00000000-0000-0000-0000-000000000000&pretty=yes",
        "results": [{
            "id": 6,
            "first_name": "Guinea",
            "last_name": "Pig",
            "full_name": "Guinea Pig"
            "email": "test@cern.ch",
            "affiliation": "CERN",
            "phone": "",
            "avatar_url": "\/user\/6\/picture-default",
            "identifier": "User:6",
        }],
    }
