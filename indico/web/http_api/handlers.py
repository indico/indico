# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
HTTP API - Handlers
"""

# python stdlib imports
import hashlib
import hmac
import re
import time
from urlparse import parse_qs
from ZODB.POSException import ConflictError
import pytz

# indico imports
from indico.web.http_api import ExportInterface
from indico.web.http_api.auth import APIKeyHolder
from indico.web.http_api.cache import RequestCache
from indico.web.http_api.fossils import IHTTPAPIResultFossil, IHTTPAPIErrorFossil
from indico.web.http_api.util import remove_lists, get_query_parameter
from indico.web.http_api import API_MODE_KEY, API_MODE_ONLYKEY, API_MODE_SIGNED, API_MODE_ONLYKEY_SIGNED, API_MODE_ALL_SIGNED
from indico.web.wsgi import webinterface_handler_config as apache
from indico.util.metadata.serializer import Serializer

# indico legacy imports
from MaKaC.common import DBMgr
from MaKaC.common.Configuration import Config
from MaKaC.common.fossilize import fossilizes, fossilize, Fossilizable
from MaKaC.accessControl import AccessWrapper
from MaKaC.common.info import HelperMaKaCInfo

# Maximum number of records that will get exported
MAX_RECORDS = 20000

# Valid URLs for export handlers. the last group has to be the response type
EXPORT_URL_MAP = {
    r'/export/(event|categ)/(\w+(?:-\w+)*)\.(\w+)$': 'handler_event_categ'
}

# Compile regexps
EXPORT_URL_MAP = dict((re.compile(pathRe), handlerFunc) for pathRe, handlerFunc in EXPORT_URL_MAP.iteritems())
RE_REMOVE_EXTENSION = re.compile(r'\.(\w+)$')

class HTTPAPIError(Exception, Fossilizable):
    fossilizes(IHTTPAPIErrorFossil)

    def getMessage(self):
        return self.message


class HTTPAPIResult(Fossilizable):
    fossilizes(IHTTPAPIResultFossil)

    def __init__(self, results, path='', query='', ts=None):
        if ts is None:
            ts = int(time.time())
        self._results = results
        self._path = path
        self._query = query
        self._ts = ts

    def getTS(self):
        return self._ts

    def getURL(self):
        prefix = Config.getInstance().getBaseSecureURL()
        if self._query:
            return prefix + self._path + '?' + self._query
        return prefix + self._path

    def getResults(self):
        return self._results

def validateSignature(req, key, signature, path, query, timestamp=None):
    if timestamp is None:
        timestamp = int(time.time())
    ts = timestamp / 300
    candidates = []
    for i in xrange(-1, 2):
        h = hmac.new(key, '%s?%s&%d' % (path, query, ts + i), hashlib.sha1)
        candidates.append(h.hexdigest())
    if signature not in candidates:
        req.status = apache.HTTP_FORBIDDEN
        raise HTTPAPIError('Signature invalid (check system clock)')

def getAK(apiKey, signature, path, query, req):
    minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
    apiMode = minfo.getAPIMode()
    if not apiKey:
        if apiMode in (API_MODE_ONLYKEY, API_MODE_ONLYKEY_SIGNED, API_MODE_ALL_SIGNED):
            req.status = apache.HTTP_FORBIDDEN
            raise HTTPAPIError('API key is missing')
        return None, True
    akh = APIKeyHolder()
    if not akh.hasKey(apiKey):
        req.status = apache.HTTP_FORBIDDEN
        raise HTTPAPIError('Invalid API key')
    ak = akh.getById(apiKey)
    if ak.isBlocked():
        req.status = apache.HTTP_FORBIDDEN
        raise HTTPAPIError('API key is blocked')
    # Signature validation
    onlyPublic = False
    if signature:
        validateSignature(req, ak.getSignKey(), signature, path, query)
    elif apiMode in (API_MODE_SIGNED, API_MODE_ALL_SIGNED):
        req.status = apache.HTTP_FORBIDDEN
        raise HTTPAPIError('Signature missing')
    elif apiMode == API_MODE_ONLYKEY_SIGNED:
        onlyPublic = True
    return ak, onlyPublic

def buildAW(ak, req, onlyPublic=False):
    aw = AccessWrapper()
    if ak and not onlyPublic:
        # If we have an authenticated request, require HTTPS
        minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
        if not req.is_https() and minfo.isAPIHTTPSRequired():
            req.status = apache.HTTP_FORBIDDEN
            raise HTTPAPIError('HTTPS is required')
        aw.setUser(ak.getUser())
    return aw

def getExportHandler(path):
    """Get the export handler, handler args and return type from a path"""
    func = None
    match = None
    for pathRe, handlerFunc in EXPORT_URL_MAP.iteritems():
        match = pathRe.match(path)
        if match:
            func = handlerFunc
            break

    groups = match and match.groups()
    if not match or groups[-1] not in ExportInterface.getAllowedFormats():
        return None, None, None
    return globals()[func], groups[:-1], groups[-1]

def handler_event_categ(dbi, aw, qdata, dtype, idlist):
    idlist = idlist.split('-')

    expInt = ExportInterface(dbi, aw)
    tzName = get_query_parameter(qdata, ['tz'], None)
    detail = get_query_parameter(qdata, ['d', 'detail'], 'events')
    limit = get_query_parameter(qdata, ['n', 'limit'], 0, integer=True)

    if tzName is None:
        info = HelperMaKaCInfo.getMaKaCInfoInstance()
        tzName = info.getTimezone()

    tz = pytz.timezone(tzName)

    # impose a hard limit
    limit = limit if limit > 0 else MAX_RECORDS

    if dtype == 'categ':
        return expInt.category(idlist, tz, limit, detail, qdata)
    elif dtype == 'event':
        return expInt.event(idlist, tz, limit, detail, qdata)

def handler(req, **params):
    path, query = req.URLFields['PATH_INFO'], req.URLFields['QUERY_STRING']
    # Extract HMAC signature
    signature = None
    m = re.search(r'&([0-9a-fA-F]{40})$', query)
    if m:
        signature = m.group(1).lower()
        query = query[:-41]

    # Parse the actual query string
    qdata = parse_qs(query)
    no_cache = get_query_parameter(qdata, ['nc', 'nocache'], 'no') == 'yes'

    # Copy qdata for the cache key
    qdata_copy = dict(qdata)
    cache = RequestCache()

    dbi = DBMgr.getInstance()
    dbi.startRequest()

    pretty = get_query_parameter(qdata, ['p', 'pretty'], 'no') == 'yes'
    apiKey = get_query_parameter(qdata, ['ak', 'apikey'], None)
    onlyPublic = get_query_parameter(qdata, ['op', 'onlypublic'], 'no') == 'yes'

    # Get our handler function and its argument and response type
    func, args, dformat = getExportHandler(path)
    if func is None or dformat is None:
        raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND

    ak = error = results = None
    ts = int(time.time())
    try:
        # Validate the API key (and its signature)
        ak, enforceOnlyPublic = getAK(apiKey, signature, path, query, req)
        if enforceOnlyPublic:
            onlyPublic = True
        # Create an access wrapper for the API key's user
        aw = buildAW(ak, req, onlyPublic)
        # Get rid of API key in cache key if we did not impersonate a user
        if ak and aw.getUser() is None:
            qdata_copy.pop('ak', None)
            qdata_copy.pop('apikey', None)

        obj = None
        add_to_cache = True
        cache_path = RE_REMOVE_EXTENSION.sub('', path)
        if not no_cache:
            obj = cache.loadObject(cache_path, qdata_copy)
            if obj is not None:
                results = obj.getContent()
                ts = obj.getTS()
                add_to_cache = False
        if results is None:
            # Perform the actual exporting
            results = func(dbi, aw, qdata, *args)
        if results is not None and add_to_cache:
            cache.cacheObject(cache_path, qdata_copy, results)
    except HTTPAPIError, e:
        error = e

    if results is None and error is None:
        # TODO: usage page
        raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND
    else:
        if ak and error is None:
            # Commit only if there was an API key and no error
            for _retry in xrange(10):
                dbi.sync()
                ak.used(req.remote_ip, path, query, not onlyPublic)
                try:
                    dbi.endRequest(True)
                except ConflictError:
                    pass # retry
                else:
                    break
        else:
            # No need to commit stuff if we didn't use an API key
            # (nothing was written)
            dbi.endRequest(False)

        serializer = Serializer.create(dformat, pretty=pretty,
                                       **remove_lists(qdata))

        if error:
            resultFossil = fossilize(error)
        else:
            resultFossil = fossilize(HTTPAPIResult(results, path, query, ts))
        del resultFossil['_fossil']

        req.headers_out['Content-Type'] = serializer.getMIMEType()
        return serializer(resultFossil)
