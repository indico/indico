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


def buildAW(apiKey):
    user = None
    aw = AccessWrapper()
    ak = None
    akh = APIKeyHolder()

    if apiKey:
        if akh.hasKey(apiKey):
            ak = APIKeyHolder().getById(apiKey)
            if ak.isBlocked():
                req.status = apache.HTTP_FORBIDDEN
                return 'API key is blocked'
            user = ak.getUser()
            aw.setUser(user)
            return ak, aw
        else:
            req.status = apache.HTTP_FORBIDDEN
            return 'Invalid API key'
    else:
        return None, None


def handler(req, **params):
    path, query = req.URLFields['PATH_INFO'], req.URLFields['QUERY_STRING']
    qdata = parse_qs(query)
    no_cache = get_query_parameter(qdata, ['nc', 'nocache'], 'no') == 'yes'

    # Copy qdata for the cache key
    qdata_copy = dict(qdata)
    cache = RequestCache()
    obj = None
    if not no_cache:
        obj = cache.loadObject(path, qdata_copy)

    resp = None
    from_cache = False

    if obj is not None:
        resp = obj.getContent()
        from_cache = True
    else:
        dbi = DBMgr.getInstance()
        dbi.startRequest()

        pretty = get_query_parameter(qdata, ['p', 'pretty'], 'no') == 'yes'
        apiKey = get_query_parameter(qdata, ['ak', 'apikey'], None)

        # get an API key and an API key holder ou of the parameter
        ak, aw = buildAW(apiKey)

        results = None
        m = re.match(r'/export/(event|categ)/(\w+(?:-\w+)*)\.(\w+)/?$', path)

        if m and m.group(3) in ExportInterface.getAllowedFormats():
            dtype, idlist, dformat = m.groups()
            idlist = idlist.split('-')

            expInt = ExportInterface(dbi, aw)
            tzName = get_query_parameter(qdata, ['tz'], None)
            detail = get_query_parameter(qdata, ['d', 'detail'], 'events')
            limit = get_query_parameter(qdata, ['n', 'limit'], 0, integer=True)

            if tzName == None:
                info = HelperMaKaCInfo.getMaKaCInfoInstance()
                tzName = info.getTimezone()

            tz = pytz.timezone(tzName)

            # impose a hard limit
            limit = limit if limit > 0 else MAX_RECORDS

            if dtype == 'categ':
                results = expInt.category(idlist, tz, limit, detail, qdata)
            elif dtype == 'event':
                results = expInt.event(idlist, tz, limit, detail, qdata)
            else:
                results = None

        else:
            results = None

        if results == None:
            # TODO: usage page
            raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND
        else:
            serializer = Serializer.create(dformat, pretty=pretty,
                                           **remove_lists(qdata))

            if ak:
                for _retry in xrange(10):
                    dbi.sync()
                    ak.used(req.remote_ip, path, query)
                    try:
                        dbi.endRequest(True)
                    except ConflictError:
                        pass  # retry
                    else:
                        break

                resultFossil = fossilize(HTTPAPIResult(results, path, query))
                del resultFossil['_fossil']
                result = serializer(resultFossil)

            else:
                # No need to commit stuff if we didn't use an API key
                # (nothing was written)
                dbi.endRequest(False)
                error = HTTPAPIError("Access key is invalid!")
                if serializer.schemaless:
                    result = serializer(fossilize(error))
                else:
                    result = str(error)

        resp = serializer.getMIMEType(), result

    if not from_cache:
        cache.cacheObject(path, qdata_copy, resp)
    req.headers_out['Content-Type'] = resp[0]
    return resp[1]
