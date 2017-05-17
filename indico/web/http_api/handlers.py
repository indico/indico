# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

"""
HTTP API - Handlers
"""

import hashlib
import hmac
import posixpath
import re
import time
import urllib
from uuid import UUID

from flask import request, session, g, current_app
from urlparse import parse_qs
from werkzeug.exceptions import NotFound, BadRequest

from indico.core.config import Config
from indico.core.db import db
from indico.core.logger import Logger
from indico.modules.api import APIMode
from indico.modules.api import api_settings
from indico.modules.api.models.keys import APIKey
from indico.modules.oauth import oauth
from indico.modules.oauth.provider import load_token
from indico.util.string import to_unicode
from indico.web.http_api import HTTPAPIHook
from indico.web.http_api.responses import HTTPAPIResult, HTTPAPIError
from indico.web.http_api.util import get_query_parameter
from indico.web.http_api.fossils import IHTTPAPIExportResultFossil
from indico.web.http_api.metadata.serializer import Serializer
from indico.web.flask.util import ResponseUtil

from indico.legacy.common.fossilize import fossilize, clearCache
from indico.legacy.accessControl import AccessWrapper
from indico.legacy.common.cache import GenericCache


# Remove the extension at the end or before the querystring
RE_REMOVE_EXTENSION = re.compile(r'\.(\w+)(?:$|(?=\?))')


def normalizeQuery(path, query, remove=('signature',), separate=False):
    """Normalize request path and query so it can be used for caching and signing

    Returns a string consisting of path and sorted query string.
    Dynamic arguments like signature and timestamp are removed from the query string.
    """
    qparams = parse_qs(query)
    sorted_params = []

    for key, values in sorted(qparams.items(), key=lambda x: x[0].lower()):
        key = key.lower()
        if key not in remove:
            for v in sorted(values):
                sorted_params.append((key, v))

    if separate:
        return path, sorted_params and urllib.urlencode(sorted_params)
    elif sorted_params:
        return '%s?%s' % (path, urllib.urlencode(sorted_params))
    else:
        return path


def validateSignature(ak, signature, timestamp, path, query):
    ttl = api_settings.get('signature_ttl')
    if not timestamp and not (ak.is_persistent_allowed and api_settings.get('allow_persistent')):
        raise HTTPAPIError('Signature invalid (no timestamp)', 403)
    elif timestamp and abs(timestamp - int(time.time())) > ttl:
        raise HTTPAPIError('Signature invalid (bad timestamp)', 403)
    digest = hmac.new(ak.secret, normalizeQuery(path, query), hashlib.sha1).hexdigest()
    if signature != digest:
        raise HTTPAPIError('Signature invalid', 403)


def checkAK(apiKey, signature, timestamp, path, query):
    apiMode = api_settings.get('security_mode')
    if not apiKey:
        if apiMode in {APIMode.ONLYKEY, APIMode.ONLYKEY_SIGNED, APIMode.ALL_SIGNED}:
            raise HTTPAPIError('API key is missing', 403)
        return None, True
    try:
        UUID(hex=apiKey)
    except ValueError:
        raise HTTPAPIError('Malformed API key', 400)
    ak = APIKey.find_first(token=apiKey, is_active=True)
    if not ak:
        raise HTTPAPIError('Invalid API key', 403)
    if ak.is_blocked:
        raise HTTPAPIError('API key is blocked', 403)
    # Signature validation
    onlyPublic = False
    if signature:
        validateSignature(ak, signature, timestamp, path, query)
    elif apiMode == APIMode.ALL_SIGNED:
        raise HTTPAPIError('Signature missing', 403)
    elif apiMode in {APIMode.SIGNED, APIMode.ONLYKEY_SIGNED}:
        onlyPublic = True
    return ak, onlyPublic


def buildAW(ak, onlyPublic=False):
    aw = AccessWrapper()
    if ak and not onlyPublic:
        aw.setUser(ak.user.as_avatar)
    return aw


def handler(prefix, path):
    path = posixpath.join('/', prefix, path)
    clearCache()  # init fossil cache
    logger = Logger.get('httpapi')
    if request.method == 'POST':
        # Convert POST data to a query string
        queryParams = [(key, [x.encode('utf-8') for x in values]) for key, values in request.form.iterlists()]
        query = urllib.urlencode(queryParams, doseq=1)
        # we only need/keep multiple values so we can properly validate the signature.
        # the legacy code below expects a dict with just the first value.
        # if you write a new api endpoint that needs multiple values get them from
        # ``request.values.getlist()`` directly
        queryParams = {key: values[0] for key, values in queryParams}
    else:
        # Parse the actual query string
        queryParams = dict((key, value.encode('utf-8')) for key, value in request.args.iteritems())
        query = request.query_string

    apiKey = get_query_parameter(queryParams, ['ak', 'apikey'], None)
    cookieAuth = get_query_parameter(queryParams, ['ca', 'cookieauth'], 'no') == 'yes'
    signature = get_query_parameter(queryParams, ['signature'])
    timestamp = get_query_parameter(queryParams, ['timestamp'], 0, integer=True)
    noCache = get_query_parameter(queryParams, ['nc', 'nocache'], 'no') == 'yes'
    pretty = get_query_parameter(queryParams, ['p', 'pretty'], 'no') == 'yes'
    onlyPublic = get_query_parameter(queryParams, ['op', 'onlypublic'], 'no') == 'yes'
    onlyAuthed = get_query_parameter(queryParams, ['oa', 'onlyauthed'], 'no') == 'yes'
    scope = 'read:legacy_api' if request.method == 'GET' else 'write:legacy_api'
    try:
        oauth_valid, oauth_request = oauth.verify_request([scope])
        if not oauth_valid and oauth_request and oauth_request.error_message != 'Bearer token not found.':
            raise BadRequest('OAuth error: {}'.format(oauth_request.error_message))
        elif g.get('received_oauth_token') and oauth_request.error_message == 'Bearer token not found.':
            raise BadRequest('OAuth error: Invalid token')
    except ValueError:
        # XXX: Dirty hack to workaround a bug in flask-oauthlib that causes it
        #      not to properly urlencode request query strings
        #      Related issue (https://github.com/lepture/flask-oauthlib/issues/213)
        oauth_valid = False

    # Get our handler function and its argument and response type
    hook, dformat = HTTPAPIHook.parseRequest(path, queryParams)
    if hook is None or dformat is None:
        raise NotFound

    # Disable caching if we are not just retrieving data (or the hook requires it)
    if request.method == 'POST' or hook.NO_CACHE:
        noCache = True

    ak = error = result = None
    ts = int(time.time())
    typeMap = {}
    responseUtil = ResponseUtil()
    is_response = False
    try:
        used_session = None
        if cookieAuth:
            used_session = session
            if not used_session.user:  # ignore guest sessions
                used_session = None

        if apiKey or oauth_valid or not used_session:
            if not oauth_valid:
                # Validate the API key (and its signature)
                ak, enforceOnlyPublic = checkAK(apiKey, signature, timestamp, path, query)
                if enforceOnlyPublic:
                    onlyPublic = True
                # Create an access wrapper for the API key's user
                aw = buildAW(ak, onlyPublic)
            else:  # Access Token (OAuth)
                at = load_token(oauth_request.access_token.access_token)
                aw = buildAW(at, onlyPublic)
            # Get rid of API key in cache key if we did not impersonate a user
            if ak and aw.getUser() is None:
                cacheKey = normalizeQuery(path, query,
                                          remove=('_', 'ak', 'apiKey', 'signature', 'timestamp', 'nc', 'nocache',
                                                  'oa', 'onlyauthed'))
            else:
                cacheKey = normalizeQuery(path, query,
                                          remove=('_', 'signature', 'timestamp', 'nc', 'nocache', 'oa', 'onlyauthed'))
                if signature:
                    # in case the request was signed, store the result under a different key
                    cacheKey = 'signed_' + cacheKey
        else:
            # We authenticated using a session cookie.
            if Config.getInstance().getCSRFLevel() >= 2:
                token = request.headers.get('X-CSRF-Token', get_query_parameter(queryParams, ['csrftoken']))
                if used_session.csrf_protected and used_session.csrf_token != token:
                    raise HTTPAPIError('Invalid CSRF token', 403)
            aw = AccessWrapper()
            if not onlyPublic:
                aw.setUser(used_session.avatar)
            userPrefix = 'user-{}_'.format(used_session.user.id)
            cacheKey = userPrefix + normalizeQuery(path, query,
                                                   remove=('_', 'nc', 'nocache', 'ca', 'cookieauth', 'oa', 'onlyauthed',
                                                           'csrftoken'))

        # Bail out if the user requires authentication but is not authenticated
        if onlyAuthed and not aw.getUser():
            raise HTTPAPIError('Not authenticated', 403)

        addToCache = not hook.NO_CACHE
        cache = GenericCache('HTTPAPI')
        cacheKey = RE_REMOVE_EXTENSION.sub('', cacheKey)
        if not noCache:
            obj = cache.get(cacheKey)
            if obj is not None:
                result, extra, ts, complete, typeMap = obj
                addToCache = False
        if result is None:
            g.current_api_user = aw.user
            # Perform the actual exporting
            res = hook(aw)
            if isinstance(res, current_app.response_class):
                addToCache = False
                is_response = True
                result, extra, complete, typeMap = res, {}, True, {}
            elif isinstance(res, tuple) and len(res) == 4:
                result, extra, complete, typeMap = res
            else:
                result, extra, complete, typeMap = res, {}, True, {}
        if result is not None and addToCache:
            ttl = api_settings.get('cache_ttl')
            if ttl > 0:
                cache.set(cacheKey, (result, extra, ts, complete, typeMap), ttl)
    except HTTPAPIError, e:
        error = e
        if e.getCode():
            responseUtil.status = e.getCode()
            if responseUtil.status == 405:
                responseUtil.headers['Allow'] = 'GET' if request.method == 'POST' else 'POST'

    if result is None and error is None:
        # TODO: usage page
        raise NotFound
    else:
        if ak and error is None:
            # Commit only if there was an API key and no error
            norm_path, norm_query = normalizeQuery(path, query, remove=('signature', 'timestamp'), separate=True)
            uri = to_unicode('?'.join(filter(None, (norm_path, norm_query))))
            ak.register_used(request.remote_addr, uri, not onlyPublic)
            db.session.commit()
        else:
            # No need to commit stuff if we didn't use an API key (nothing was written)
            # XXX do we even need this?
            db.session.rollback()

        # Log successful POST api requests
        if error is None and request.method == 'POST':
            logger.info('API request: %s?%s', path, query)
        if is_response:
            return result
        serializer = Serializer.create(dformat, query_params=queryParams, pretty=pretty, typeMap=typeMap,
                                       **hook.serializer_args)
        if error:
            if not serializer.schemaless:
                # if our serializer has a specific schema (HTML, ICAL, etc...)
                # use JSON, since it is universal
                serializer = Serializer.create('json')

            result = fossilize(error)
        else:
            if serializer.encapsulate:
                result = fossilize(HTTPAPIResult(result, path, query, ts, complete, extra), IHTTPAPIExportResultFossil)
                del result['_fossil']

        try:
            data = serializer(result)
            serializer.set_headers(responseUtil)
            return responseUtil.make_response(data)
        except:
            logger.exception('Serialization error in request %s?%s', path, query)
            raise
