Accessing the API
=================

URL structure
-------------

Indico allows you to programmatically access the content of its
database by exposing various information like category contents, events,
rooms and room bookings through a web service, the HTTP Export API.

The basic URL looks like:

http://my.indico.server/export/WHAT/[LOC/]ID.TYPE?PARAMS&ak=KEY&timestamp=TS&signature=SIG

where:

* *WHAT* is the element you want to export (one of *categ*, *event*, *room*, *reservation*)
* *LOC* is the location of the element(s) specified by *ID* and only used
  for certain elements, for example, for the room booking (https://indico.server/export/room/CERN/120.json?ak=0...)
* *ID* is the ID of the element you want to export (can be a *-* separated list). As for example, the 120 in the above URL.
* *TYPE* is the output format (one of *json*, *jsonp*, *xml*, *html*, *ics*, *atom*, *bin*)
* *PARAMS* are various parameters affecting (filtering, sorting, ...) the
  result list
* *KEY*, *TS*, *SIG* are part of the :ref:`api-authentication`.


Some examples could be:

 * Export data about events in a category: https://my.indico/export/categ/2.json?from=today&to=today&pretty=yes
 * Export data about a event: https://indico.server/export/event/137346.json?occ=yes&pretty=yes
 * Export data about rooms: https://indico.server/export/room/CERN/120.json?ak=00000000-0000-0000-0000-000000000000&pretty=yes
 * Export your reservations: https://indico.server/export/reservation/CERN.json?ak=00000000-0000-0000-0000-000000000000&detail=reservations&from=today&to=today&bookedfor=USERNAME&pretty=yes


See more details about querying in `Exporters <exporters/index.html>`_.

.. _api-authentication:

API Authentication
------------------

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
