Accessing the API
=================

URL structure
-------------

Indico allows you to programmatically access the content of its
database by exposing various information like category contents, events,
rooms and room bookings through a web service, the HTTP Export API.

The basic URL looks like:

``https://my.indico.server/export/WHAT/[LOC/]ID.TYPE?PARAMS``

or when using legacy API keys:

``https://my.indico.server/export/WHAT/[LOC/]ID.TYPE?PARAMS&ak=KEY&timestamp=TS&signature=SIG``

where:

* *WHAT* is the element you want to export (one of *categ*, *event*, *room*, *reservation*)
* *LOC* is the location of the element(s) specified by *ID* and only used
  for certain elements, for example, for the room booking (https://indico.server/export/room/CERN/120.json?ak=0...)
* *ID* is the ID of the element you want to export (can be a *-* separated list). As for example, the 120 in the above URL.
* *TYPE* is the output format (one of *json*, *jsonp*, *xml*, *html*, *ics*, *atom*, *bin*)
* *PARAMS* are various parameters affecting (filtering, sorting, ...) the
  result list
* *KEY*, *TS*, *SIG* are part of the :ref:`api-authentication-legacy`


Some examples could be:

 * Export data about events in a category: ``/export/categ/2.json?from=today&to=today&pretty=yes``
 * Export data about a event: ``/export/event/137346.json?occ=yes&pretty=yes``
 * Export data about rooms: ``/export/room/CERN/120.json?pretty=yes``
 * Export your reservations: ``/export/reservation/CERN.json?detail=reservations&from=today&to=today&bookedfor=USERNAME&pretty=yes``


See more details about querying in :doc:`exporters/index`.

.. _api-authentication:

API Token Authentication
------------------------

.. versionadded:: 3.0

Indico users may create API tokens with a custom name and scope. They can then be used to authenticate
requests to the Indico API using the standard ``Authorization: Bearer <token>`` HTTP header.

Compared to the legacy API key authentication (see below), they have various advantages:

- no need to generate signatures and deal with expiring links - nowadays with HTTPS being widespread,
  the risk of leaking a link (but not the secrets used to generate it) is very low
- authentication using a HTTP header avoids including sensitive information in the query string
- each application/script can get its own token, which can have only the scopes assigned that are actually
  needed
- they behave exactly like OAuth tokens, except that no OAuth application or OAuth flow is required, which
  makes them perfect for use in custom scripts

These personal API tokens always have the format ``indp_<42 random chars>`` - tokens generated during a regular
OAuth flow have the ``indo_`` prefix instead.

.. note::

    Indico administrators have the ability to restrict the creation of API tokens; in that case only
    admins can create tokens or manage their scopes, but users who have a token can still reset it in
    order to use the API once authorized by an admin.

Scopes
~~~~~~

API tokens can have one or more of these scopes:

.. exec::
    def main():
        from indico.core.oauth.scopes import SCOPES
        for name, desc in sorted(SCOPES.items(), key=lambda x: x[0].split(':')[::-1]):
            print(f'- ``{name}`` - {desc}')

    main()

The ``everything`` scopes are special because they can be used with *any* Indico endpoint (including file attachments),
i.e. they are not restricted to official APIs. This has the advantage that even Indico actions which do not have a
corresponding API can be scripted.
Endpoints covered by the ``legacy_api`` scopes are *not* included; these scopes need to be granted explicitly.

.. warning::

    We make absolutely no promises of backwards compatibility on endpoints that are not part of documented APIs.
    You use them at your own risk.

The ``legacy_api`` scopes grant access to the API this documentation is about, i.e. ``/export/`` for retrieving
data and some ``/api/`` paths for modifying data.

The ``read:user`` scope grants access to basic information about the current user via the ``/api/user/`` endpoint:

.. code-block:: json

    {
        "admin": false,
        "email": "guinea.pig@example.com",
        "first_name": "Guinea",
        "id": 1337,
        "last_name": "Pig"
    }

The ``registrants`` scope is mainly used by the mobile check-in app and grants access to (currently) undocumented
APIs that allow retrieving the list of registrants in an event and and updating their check-in state.


.. _api-authentication-legacy:

API Key Authentication (Deprecated)
-----------------------------------

.. deprecated:: 3.0

    Use :ref:`api-authentication` instead. This authentication method may be removed in a future version.

General
~~~~~~~

The HTTP Export API uses an API key and - depending on the config - a
cryptographic signature for each request.

To create an API key, go to *My Profile » HTTP API* and click the
*Create API key* button. This will create an *API Key* and a *Secret Key*
(if signatures are required).

It is recommended to always use the highest security level. That means if
only an *API key* is available always include it and if a *secret key* is
available, always sign your requests. Since you might want to retrieve only
public information (instead of everything visible to your Indico user) you
can add the param *onlypublic=yes* to the query string.

It is also possible to re-use the existing Indico session. This only makes
sense if your browser accesses the API, e.g. because you are developing on
Indico and want to access the API via an AJAX request. Additionally this method
of authentication is restricted to GET requests. To use it, add *cookieauth=yes*
to the query string and do not specify an API key, timestamp or signature.
To prevent data leakage via CSRF the CSRF token of the current session needs to
be provided as a GET argument *csrftoken* or a HTTP header *X-CSRF-Token*.

Request Signing
~~~~~~~~~~~~~~~

To sign a request, you need the following:

* The requested path, e.g. */export/categ/123.json*
* Any additional params, e.g. *limit=10*
* The current UNIX timestamp
* Your *API key* and *secret key*

1) Add your API key to the params (*limit=10&ak=your-api-key*)
2) Add the current timestamp to the params (*limit=10&ak=your-api-key&timestamp=1234567890*)
3) Sort the query string params (*ak=your-api-key&limit=10&timestamp=1234567890*)
4) Merge path and the sorted query string to a single string (*/export/categ/123.json?ak=your-api-key&limit=10&timestamp=1234567890*)
5) Create a HMAC-SHA1 signature of this string using your *secret key* as
   the key.
6) Append the hex-encoded signature to your query string: *?ak=your-api-key&limit=10&timestamp=1234567890&signature=your-signature*

Note that a signed request might be valid only for a few seconds or
minutes, so you **need** to sign it right before sending it and not store
the generated URL as it is likely to expire soon.

You can find example code for Python and PHP in the following sections.

If persistent signatures are enabled, you can also omit the timestamp.
In this case the URL is valid forever. When using this feature, please
make sure to use these URLs only where necessary - use timestamped
URLs whenever possible.

Request Signing for Python
^^^^^^^^^^^^^^^^^^^^^^^^^^

A simple example in Python::

    import hashlib
    import hmac
    import time

    try:
        from urllib.parse import urlencode
    except ImportError:
        from urllib import urlencode


    def build_indico_request(path, params, api_key=None, secret_key=None, only_public=False, persistent=False):
        items = list(params.items()) if hasattr(params, 'items') else list(params)
        if api_key:
            items.append(('apikey', api_key))
        if only_public:
            items.append(('onlypublic', 'yes'))
        if secret_key:
            if not persistent:
                items.append(('timestamp', str(int(time.time()))))
            items = sorted(items, key=lambda x: x[0].lower())
            url = '%s?%s' % (path, urlencode(items))
            signature = hmac.new(secret_key.encode('utf-8'), url.encode('utf-8'),
                                 hashlib.sha1).hexdigest()
            items.append(('signature', signature))
        if not items:
            return path
        return '%s?%s' % (path, urlencode(items))


    if __name__ == '__main__':
        API_KEY = '00000000-0000-0000-0000-000000000000'
        SECRET_KEY = '00000000-0000-0000-0000-000000000000'
        PATH = '/export/categ/1337.json'
        PARAMS = {
            'limit': 123
        }
        print(build_indico_request(PATH, PARAMS, API_KEY, SECRET_KEY))

Request Signing for PHP
^^^^^^^^^^^^^^^^^^^^^^^

A simple example in PHP::

    <?php

    function build_indico_request($path, $params, $api_key = null, $secret_key = null, $only_public = false, $persistent = false) {
        if($api_key) {
            $params['apikey'] = $api_key;
        }

        if($only_public) {
            $params['onlypublic'] = 'yes';
        }

        if($secret_key) {
            if(!$persistent) {
                $params['timestamp'] = time();
            }
            uksort($params, 'strcasecmp');
            $url = $path . '?' . http_build_query($params);
            $params['signature'] = hash_hmac('sha1', $url, $secret_key);
        }

        if(!$params) {
            return $path;
        }

        return $path . '?' . http_build_query($params);
    }

    if(true) { // change to false if you want to include this file
        $API_KEY = '00000000-0000-0000-0000-000000000000';
        $SECRET_KEY = '00000000-0000-0000-0000-000000000000';
        $PATH = '/export/categ/1337.json';
        $PARAMS = array(
            'limit' => 123
        );
        echo build_indico_request($PATH, $PARAMS, $API_KEY, $SECRET_KEY) . "\n";
    }
