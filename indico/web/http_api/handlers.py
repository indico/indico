# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

"""
HTTP API - Handlers
"""

# python stdlib imports
import hashlib
import hmac
import posixpath
import re
import time
import urllib
from flask import request, session
from urlparse import parse_qs
from ZODB.POSException import ConflictError

# indico imports
from werkzeug.exceptions import NotFound
from indico.web.http_api import HTTPAPIHook
from indico.web.http_api.auth import APIKeyHolder
from indico.web.http_api.responses import HTTPAPIResult, HTTPAPIError
from indico.web.http_api.util import get_query_parameter
from indico.web.http_api import API_MODE_ONLYKEY, API_MODE_SIGNED, API_MODE_ONLYKEY_SIGNED, API_MODE_ALL_SIGNED
from indico.web.http_api.fossils import IHTTPAPIExportResultFossil
from indico.web.http_api.metadata.serializer import Serializer
from indico.web.flask.util import ResponseUtil
from indico.util.contextManager import ContextManager
from indico.modules.oauth.errors import OAuthError
from indico.modules.oauth.components import OAuthUtils

# indico legacy imports
from indico.core.db import DBMgr
from indico.core.config import Config
from MaKaC.common.logger import Logger
from MaKaC.common.fossilize import fossilize, clearCache
from MaKaC.accessControl import AccessWrapper
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.common.cache import GenericCache
from MaKaC.plugins.RoomBooking.default.factory import Factory
from MaKaC.authentication.LDAPAuthentication import LDAPConnector


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


def validateSignature(ak, minfo, signature, timestamp, path, query):
    ttl = HelperMaKaCInfo.getMaKaCInfoInstance().getAPISignatureTTL()
    if not timestamp and not (ak.isPersistentAllowed() and minfo.isAPIPersistentAllowed()):
        raise HTTPAPIError('Signature invalid (no timestamp)', 403)
    elif timestamp and abs(timestamp - int(time.time())) > ttl:
        raise HTTPAPIError('Signature invalid (bad timestamp)', 403)
    digest = hmac.new(ak.getSignKey(), normalizeQuery(path, query), hashlib.sha1).hexdigest()
    if signature != digest:
        raise HTTPAPIError('Signature invalid', 403)


def checkAK(apiKey, signature, timestamp, path, query):
    minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
    apiMode = minfo.getAPIMode()
    if not apiKey:
        if apiMode in (API_MODE_ONLYKEY, API_MODE_ONLYKEY_SIGNED, API_MODE_ALL_SIGNED):
            raise HTTPAPIError('API key is missing', 403)
        return None, True
    akh = APIKeyHolder()
    if not akh.hasKey(apiKey):
        raise HTTPAPIError('Invalid API key', 403)
    ak = akh.getById(apiKey)
    if ak.isBlocked():
        raise HTTPAPIError('API key is blocked', 403)
    # Signature validation
    onlyPublic = False
    if signature:
        validateSignature(ak, minfo, signature, timestamp, path, query)
    elif apiMode == API_MODE_ALL_SIGNED:
        raise HTTPAPIError('Signature missing', 403)
    elif apiMode in (API_MODE_SIGNED, API_MODE_ONLYKEY_SIGNED):
        onlyPublic = True
    return ak, onlyPublic


def buildAW(ak, onlyPublic=False):
    aw = AccessWrapper()
    aw.setIP(str(request.remote_addr))
    if ak and not onlyPublic:
        # If we have an authenticated request, require HTTPS
        minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
        # Dirty hack: Google calendar converts HTTP API requests from https to http
        # Therefore, not working with Indico setup (requiring https for HTTP API authenticated)
        if not request.is_secure and minfo.isAPIHTTPSRequired() and request.user_agent.browser != 'google':
            raise HTTPAPIError('HTTPS is required', 403)
        aw.setUser(ak.getUser())
    return aw


def handler(prefix, path):
    path = posixpath.join('/', prefix, path)
    ContextManager.destroy()
    clearCache()  # init fossil cache
    logger = Logger.get('httpapi')
    if request.method == 'POST':
        # Convert POST data to a query string
        queryParams = dict((key, value.encode('utf-8')) for key, value in request.form.iteritems())
        query = urllib.urlencode(queryParams)
    else:
        # Parse the actual query string
        queryParams = dict((key, value.encode('utf-8')) for key, value in request.args.iteritems())
        query = request.query_string

    dbi = DBMgr.getInstance()
    dbi.startRequest()
    minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
    if minfo.getRoomBookingModuleActive():
        Factory.getDALManager().connect()

    apiKey = get_query_parameter(queryParams, ['ak', 'apikey'], None)
    cookieAuth = get_query_parameter(queryParams, ['ca', 'cookieauth'], 'no') == 'yes'
    signature = get_query_parameter(queryParams, ['signature'])
    timestamp = get_query_parameter(queryParams, ['timestamp'], 0, integer=True)
    noCache = get_query_parameter(queryParams, ['nc', 'nocache'], 'no') == 'yes'
    pretty = get_query_parameter(queryParams, ['p', 'pretty'], 'no') == 'yes'
    onlyPublic = get_query_parameter(queryParams, ['op', 'onlypublic'], 'no') == 'yes'
    onlyAuthed = get_query_parameter(queryParams, ['oa', 'onlyauthed'], 'no') == 'yes'
    oauthToken = 'oauth_token' in queryParams
    # Check if OAuth data is supplied in the Authorization header
    if not oauthToken and request.headers.get('Authorization') is not None:
        oauthToken = 'oauth_token' in request.headers.get('Authorization')

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
    try:
        used_session = None
        if cookieAuth:
            used_session = session
            if not used_session.user:  # ignore guest sessions
                used_session = None

        if apiKey or oauthToken or not used_session:
            if not oauthToken:
                # Validate the API key (and its signature)
                ak, enforceOnlyPublic = checkAK(apiKey, signature, timestamp, path, query)
                if enforceOnlyPublic:
                    onlyPublic = True
                # Create an access wrapper for the API key's user
                aw = buildAW(ak, onlyPublic)
            else:  # Access Token (OAuth)
                at = OAuthUtils.OAuthCheckAccessResource()
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
                aw.setUser(used_session.user)
            userPrefix = 'user-' + used_session.user.getId() + '_'
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
            ContextManager.set("currentAW", aw)
            # Perform the actual exporting
            res = hook(aw)
            if isinstance(res, tuple) and len(res) == 4:
                result, extra, complete, typeMap = res
            else:
                result, extra, complete, typeMap = res, {}, True, {}
        if result is not None and addToCache:
            ttl = HelperMaKaCInfo.getMaKaCInfoInstance().getAPICacheTTL()
            cache.set(cacheKey, (result, extra, ts, complete, typeMap), ttl)
    except HTTPAPIError, e:
        error = e
        if e.getCode():
            responseUtil.status = e.getCode()
            if responseUtil.status == 405:
                responseUtil.headers['Allow'] = 'GET' if request.method == 'POST' else 'POST'
    except OAuthError, e:
        error = e
        if e.getCode():
            responseUtil.status = e.getCode()

    if result is None and error is None:
        # TODO: usage page
        raise NotFound
    else:
        if ak and error is None:
            # Commit only if there was an API key and no error
            for _retry in xrange(10):
                dbi.sync()
                if minfo.getRoomBookingModuleActive():
                    Factory.getDALManager().sync()
                normPath, normQuery = normalizeQuery(path, query, remove=('signature', 'timestamp'), separate=True)
                ak.used(request.remote_addr, normPath, normQuery, not onlyPublic)
                try:
                    if minfo.getRoomBookingModuleActive():
                        Factory.getDALManager().disconnect()
                    dbi.endRequest(True)
                except ConflictError:
                    pass  # retry
                else:
                    break
        else:
            # No need to commit stuff if we didn't use an API key
            # (nothing was written)
            if minfo.getRoomBookingModuleActive():
                Factory.getDALManager().rollback()
                Factory.getDALManager().disconnect()
            dbi.endRequest(False)

        LDAPConnector.destroy()

        # Log successful POST api requests
        if error is None and request.method == 'POST':
            logger.info('API request: %s?%s' % (path, query))

        serializer = Serializer.create(dformat, pretty=pretty, typeMap=typeMap,
                                       **queryParams)
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
            logger.exception('Serialization error in request %s?%s' % (path, query))
            raise
