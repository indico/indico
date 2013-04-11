# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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
import re
import time
import urllib
from urlparse import parse_qs
from ZODB.POSException import ConflictError

# indico imports
from indico.web.http_api import HTTPAPIHook
from indico.web.http_api.auth import APIKeyHolder
from indico.web.http_api.responses import HTTPAPIResult, HTTPAPIError
from indico.web.http_api.util import remove_lists, get_query_parameter
from indico.web.http_api import API_MODE_ONLYKEY, API_MODE_SIGNED, API_MODE_ONLYKEY_SIGNED, API_MODE_ALL_SIGNED
from indico.web.http_api.fossils import IHTTPAPIExportResultFossil
from indico.web.wsgi import webinterface_handler_config as apache
from indico.web.http_api.metadata.serializer import Serializer
from indico.util.network import _get_remote_ip
from indico.util.contextManager import ContextManager

# indico legacy imports
from MaKaC.common import DBMgr
from MaKaC.common.logger import Logger
from MaKaC.common.fossilize import fossilize
from MaKaC.accessControl import AccessWrapper
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.common.cache import GenericCache
from MaKaC.plugins.RoomBooking.default.factory import Factory


# Remove the extension at the end or before the querystring
RE_REMOVE_EXTENSION = re.compile(r'\.(\w+)(?:$|(?=\?))')


def normalizeQuery(path, query, remove=('signature',), separate=False):
    """Normalize request path and query so it can be used for caching and signing

    Returns a string consisting of path and sorted query string.
    Dynamic arguments like signature and timestamp are removed from the query string.
    """
    queryParams = remove_lists(parse_qs(query))
    if remove:
        for key in remove:
            queryParams.pop(key, None)
    sortedQuery = sorted(queryParams.items(), key=lambda x: x[0].lower())
    if separate:
        return path, sortedQuery and urllib.urlencode(sortedQuery)
    elif sortedQuery:
        return '%s?%s' % (path, urllib.urlencode(sortedQuery))
    else:
        return path


def validateSignature(ak, minfo, signature, timestamp, path, query):
    ttl = HelperMaKaCInfo.getMaKaCInfoInstance().getAPISignatureTTL()
    if not timestamp and not (ak.isPersistentAllowed() and minfo.isAPIPersistentAllowed()):
        raise HTTPAPIError('Signature invalid (no timestamp)', apache.HTTP_FORBIDDEN)
    elif timestamp and abs(timestamp - int(time.time())) > ttl:
        raise HTTPAPIError('Signature invalid (bad timestamp)', apache.HTTP_FORBIDDEN)
    digest = hmac.new(ak.getSignKey(), normalizeQuery(path, query), hashlib.sha1).hexdigest()
    if signature != digest:
        raise HTTPAPIError('Signature invalid', apache.HTTP_FORBIDDEN)


def checkAK(apiKey, signature, timestamp, path, query):
    minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
    apiMode = minfo.getAPIMode()
    if not apiKey:
        if apiMode in (API_MODE_ONLYKEY, API_MODE_ONLYKEY_SIGNED, API_MODE_ALL_SIGNED):
            raise HTTPAPIError('API key is missing', apache.HTTP_FORBIDDEN)
        return None, True
    akh = APIKeyHolder()
    if not akh.hasKey(apiKey):
        raise HTTPAPIError('Invalid API key', apache.HTTP_FORBIDDEN)
    ak = akh.getById(apiKey)
    if ak.isBlocked():
        raise HTTPAPIError('API key is blocked', apache.HTTP_FORBIDDEN)
    # Signature validation
    onlyPublic = False
    if signature:
        validateSignature(ak, minfo, signature, timestamp, path, query)
    elif apiMode in (API_MODE_SIGNED, API_MODE_ALL_SIGNED):
        raise HTTPAPIError('Signature missing', apache.HTTP_FORBIDDEN)
    elif apiMode == API_MODE_ONLYKEY_SIGNED:
        onlyPublic = True
    return ak, onlyPublic


def buildAW(ak, req, onlyPublic=False):
    aw = AccessWrapper()
    if ak and not onlyPublic:
        # If we have an authenticated request, require HTTPS
        minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
        # Dirty hack: Google calendar converts HTTP API requests from https to http
        # Therefore, not working with Indico setup (requiring https for HTTP API authenticated)
        if not req.is_https() and minfo.isAPIHTTPSRequired() and req.get_user_agent().find("Googlebot") == -1:
            raise HTTPAPIError('HTTPS is required', apache.HTTP_FORBIDDEN)
        aw.setUser(ak.getUser())
    return aw


def handler(req, **params):
    ContextManager.destroy()
    logger = Logger.get('httpapi')
    path, query = req.URLFields['PATH_INFO'], req.URLFields['QUERY_STRING']
    if req.method == 'POST':
        # Convert POST data to a query string
        queryParams = dict(req.form)
        for key, value in queryParams.iteritems():
            queryParams[key] = [str(value)]
        query = urllib.urlencode(remove_lists(queryParams))
    else:
        # Parse the actual query string
        queryParams = parse_qs(query)

    dbi = DBMgr.getInstance()
    dbi.startRequest()
    minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
    if minfo.getRoomBookingModuleActive():
        Factory.getDALManager().connect()

    apiKey = get_query_parameter(queryParams, ['ak', 'apikey'], None)
    signature = get_query_parameter(queryParams, ['signature'])
    timestamp = get_query_parameter(queryParams, ['timestamp'], 0, integer=True)
    noCache = get_query_parameter(queryParams, ['nc', 'nocache'], 'no') == 'yes'
    pretty = get_query_parameter(queryParams, ['p', 'pretty'], 'no') == 'yes'
    onlyPublic = get_query_parameter(queryParams, ['op', 'onlypublic'], 'no') == 'yes'

    # Get our handler function and its argument and response type
    hook, dformat = HTTPAPIHook.parseRequest(path, queryParams)
    if hook is None or dformat is None:
        raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND

    # Disable caching if we are not just retrieving data (or the hook requires it)
    if req.method == 'POST' or hook.NO_CACHE:
        noCache = True

    ak = error = result = None
    ts = int(time.time())
    typeMap = {}
    try:
        # Validate the API key (and its signature)
        ak, enforceOnlyPublic = checkAK(apiKey, signature, timestamp, path, query)
        if enforceOnlyPublic:
            onlyPublic = True
        # Create an access wrapper for the API key's user
        aw = buildAW(ak, req, onlyPublic)
        # Get rid of API key in cache key if we did not impersonate a user
        if ak and aw.getUser() is None:
            cache_key = normalizeQuery(path, query, remove=('ak', 'apiKey', 'signature', 'timestamp', 'nc', 'nocache'))
        else:
            cache_key = normalizeQuery(path, query, remove=('signature', 'timestamp', 'nc', 'nocache'))
            if signature:
                # in case the request was signed, store the result under a different key
                cache_key = 'signed_' + cache_key

        obj = None
        addToCache = not hook.NO_CACHE
        cache = GenericCache('HTTPAPI')
        cache_key = RE_REMOVE_EXTENSION.sub('', cache_key)
        if not noCache:
            obj = cache.get(cache_key)
            if obj is not None:
                result, extra, ts, complete, typeMap = obj
                addToCache = False
        if result is None:
            # Perform the actual exporting
            res = hook(aw, req)
            if isinstance(res, tuple) and len(res) == 4:
                result, extra, complete, typeMap = res
            else:
                result, extra, complete, typeMap = res, {}, True, {}
        if result is not None and addToCache:
            ttl = HelperMaKaCInfo.getMaKaCInfoInstance().getAPICacheTTL()
            cache.set(cache_key, (result, extra, ts, complete, typeMap), ttl)
    except HTTPAPIError, e:
        error = e
        if e.getCode():
            req.status = e.getCode()
            if req.status == apache.HTTP_METHOD_NOT_ALLOWED:
                req.headers_out['Allow'] = 'GET' if req.method == 'POST' else 'POST'

    if result is None and error is None:
        # TODO: usage page
        raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND
    else:
        if ak and error is None:
            # Commit only if there was an API key and no error
            for _retry in xrange(10):
                dbi.sync()
                if minfo.getRoomBookingModuleActive():
                    Factory.getDALManager().sync()
                normPath, normQuery = normalizeQuery(path, query, remove=('signature', 'timestamp'), separate=True)
                ak.used(_get_remote_ip(req), normPath, normQuery, not onlyPublic)
                try:
                    if minfo.getRoomBookingModuleActive():
                        Factory.getDALManager().disconnect()
                    dbi.endRequest(True)
                except ConflictError:
                    pass # retry
                else:
                    break
        else:
            # No need to commit stuff if we didn't use an API key
            # (nothing was written)
            if minfo.getRoomBookingModuleActive():
                Factory.getDALManager().rollback()
                Factory.getDALManager().disconnect()
            dbi.endRequest(False)

        # Log successful POST api requests
        if error is None and req.method == 'POST':
            logger.info('API request: %s?%s' % (path, query))

        serializer = Serializer.create(dformat, pretty=pretty, typeMap=typeMap,
                                       **remove_lists(queryParams))
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
            serializer.set_headers(req)

            return data
        except:
            logger.exception('Serialization error in request %s?%s' % (path, query))
            raise
