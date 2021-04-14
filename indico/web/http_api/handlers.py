# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

"""
HTTP API - Handlers
"""

import hashlib
import hmac
import posixpath
import re
import time
from urllib.parse import parse_qs, urlencode
from uuid import UUID

import sentry_sdk
from authlib.oauth2 import OAuth2Error
from flask import current_app, g, request, session
from werkzeug.exceptions import BadRequest, NotFound

from indico.core.cache import make_scoped_cache
from indico.core.db import db
from indico.core.logger import Logger
from indico.core.oauth import require_oauth
from indico.modules.api import APIMode, api_settings
from indico.modules.api.models.keys import APIKey
from indico.web.http_api import HTTPAPIHook
from indico.web.http_api.metadata.serializer import Serializer
from indico.web.http_api.responses import HTTPAPIError, HTTPAPIResult, HTTPAPIResultSchema
from indico.web.http_api.util import get_query_parameter


# Remove the extension at the end or before the querystring
RE_REMOVE_EXTENSION = re.compile(r'\.(\w+)(?:$|(?=\?))')

API_CACHE = make_scoped_cache('legacy-http-api')


def normalizeQuery(path, query, remove=('signature',), separate=False):
    """Normalize request path and query so it can be used for caching and signing.

    Returns a string consisting of path and sorted query string.
    Dynamic arguments like signature and timestamp are removed from the query string.
    """
    qparams = parse_qs(query)
    sorted_params = []

    for key, values in sorted(list(qparams.items()), key=lambda x: x[0].lower()):
        key = key.lower()
        if key not in remove:
            for v in sorted(values):
                sorted_params.append((key, v))

    if separate:
        return path, sorted_params and urlencode(sorted_params)
    elif sorted_params:
        return f'{path}?{urlencode(sorted_params)}'
    else:
        return path


def validateSignature(ak, signature, timestamp, path, query):
    ttl = api_settings.get('signature_ttl')
    if not timestamp and not (ak.is_persistent_allowed and api_settings.get('allow_persistent')):
        raise HTTPAPIError('Signature invalid (no timestamp)', 403)
    elif timestamp and abs(timestamp - int(time.time())) > ttl:
        raise HTTPAPIError('Signature invalid (bad timestamp)', 403)
    digest = hmac.new(ak.secret.encode(), normalizeQuery(path, query).encode(), hashlib.sha1).hexdigest()
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
    ak = APIKey.query.filter_by(token=apiKey, is_active=True).first()
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


def handler(prefix, path):
    path = posixpath.join('/', prefix, path)
    logger = Logger.get('httpapi')
    if request.method == 'POST':
        # Convert POST data to a query string
        queryParams = list(request.form.lists())
        query = urlencode(queryParams, doseq=1)
        # we only need/keep multiple values so we can properly validate the signature.
        # the legacy code below expects a dict with just the first value.
        # if you write a new api endpoint that needs multiple values get them from
        # ``request.values.getlist()`` directly
        queryParams = {key: values[0] for key, values in queryParams}
    else:
        # Parse the actual query string
        queryParams = {key: value for key, value in request.args.items()}
        query = request.query_string.decode()

    apiKey = get_query_parameter(queryParams, ['ak', 'apikey'], None)
    cookieAuth = get_query_parameter(queryParams, ['ca', 'cookieauth'], 'no') == 'yes'
    signature = get_query_parameter(queryParams, ['signature'])
    timestamp = get_query_parameter(queryParams, ['timestamp'], 0, integer=True)
    noCache = get_query_parameter(queryParams, ['nc', 'nocache'], 'no') == 'yes'
    pretty = get_query_parameter(queryParams, ['p', 'pretty'], 'no') == 'yes'
    onlyPublic = get_query_parameter(queryParams, ['op', 'onlypublic'], 'no') == 'yes'
    onlyAuthed = get_query_parameter(queryParams, ['oa', 'onlyauthed'], 'no') == 'yes'
    scope = 'read:legacy_api' if request.method == 'GET' else 'write:legacy_api'

    oauth_token = None
    if request.headers.get('Authorization', '').lower().startswith('bearer '):
        try:
            oauth_token = require_oauth.acquire_token([scope])
        except OAuth2Error as exc:
            raise BadRequest(f'OAuth error: {exc}')

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
    status_code = None
    is_response = False
    try:
        used_session = None
        if cookieAuth:
            used_session = session
            if not used_session.user:  # ignore guest sessions
                used_session = None

        if apiKey or oauth_token or not used_session:
            auth_token = None
            if not oauth_token:
                # Validate the API key (and its signature)
                ak, enforceOnlyPublic = checkAK(apiKey, signature, timestamp, path, query)
                if enforceOnlyPublic:
                    onlyPublic = True
                # Create an access wrapper for the API key's user
                user = ak.user if ak and not onlyPublic else None
            else:  # Access Token (OAuth)
                user = oauth_token.user if not onlyPublic else None
            # Get rid of API key in cache key if we did not impersonate a user
            if ak and user is None:
                cacheKey = normalizeQuery(path, query,
                                          remove=('_', 'ak', 'apiKey', 'signature', 'timestamp', 'nc', 'nocache',
                                                  'oa', 'onlyauthed', 'access_token'))
            else:
                cacheKey = normalizeQuery(path, query,
                                          remove=('_', 'signature', 'timestamp', 'nc', 'nocache', 'oa', 'onlyauthed',
                                                  'access_token'))
                if signature:
                    # in case the request was signed, store the result under a different key
                    cacheKey = 'signed_' + cacheKey
                if auth_token:
                    # if oauth was used, we also make the cache key unique
                    cacheKey = f'oauth-{auth_token.id}_{cacheKey}'
        else:
            # We authenticated using a session cookie.
            # XXX: This is not used anymore within indico and should be removed whenever we rewrite
            # the code here.
            token = request.headers.get('X-CSRF-Token', get_query_parameter(queryParams, ['csrftoken']))
            if used_session.csrf_protected and used_session.csrf_token != token:
                raise HTTPAPIError('Invalid CSRF token', 403)
            user = used_session.user if not onlyPublic else None
            cacheKey = normalizeQuery(path, query,
                                      remove=('_', 'nc', 'nocache', 'ca', 'cookieauth', 'oa', 'onlyauthed',
                                              'csrftoken'))

        if user is not None:
            # We *always* prefix the cache key with the user ID so we never get an overlap between
            # authenticated and unauthenticated requests
            cacheKey = f'user-{user.id}_{cacheKey}'
            sentry_sdk.set_user({
                'id': user.id,
                'email': user.email,
                'name': user.full_name,
                'source': 'http_api'
            })
        else:
            cacheKey = f'public_{cacheKey}'

        # Bail out if the user requires authentication but is not authenticated
        if onlyAuthed and not user:
            raise HTTPAPIError('Not authenticated', 403)

        addToCache = not hook.NO_CACHE
        cacheKey = RE_REMOVE_EXTENSION.sub('', cacheKey)
        if not noCache:
            obj = API_CACHE.get(cacheKey)
            if obj is not None:
                result, extra, ts, complete, typeMap = obj
                addToCache = False
        if result is None:
            g.current_api_user = user
            # Perform the actual exporting
            res = hook(user)
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
                API_CACHE.set(cacheKey, (result, extra, ts, complete, typeMap), ttl)
    except HTTPAPIError as e:
        error = e
        if e.code:
            status_code = e.code

    if result is None and error is None:
        raise NotFound
    else:
        if ak and error is None:
            # Commit only if there was an API key and no error
            norm_path, norm_query = normalizeQuery(path, query, remove=('signature', 'timestamp'), separate=True)
            uri = '?'.join([_f for _f in (norm_path, norm_query) if _f])
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

            result = {'message': error.message}
        elif serializer.encapsulate:
            result = HTTPAPIResultSchema().dump(HTTPAPIResult(result, path, query, ts, extra))

        try:
            data = serializer(result)
            response = current_app.make_response(data)
            content_type = serializer.get_response_content_type()
            if content_type:
                response.content_type = content_type
            if status_code:
                response.status_code = status_code
            return response
        except Exception:
            logger.exception('Serialization error in request %s?%s', path, query)
            raise
