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
from urlparse import parse_qs

# indico imports
from indico.web.http_api import ExportInterface
from indico.web.http_api.cache import RequestCache
from indico.web.http_api.util import remove_lists
from indico.web.wsgi import webinterface_handler_config as apache
from indico.util.metadata.serializer import Serializer

# indico legacy imports
from MaKaC.common import DBMgr


from indico.web.http_api.util import get_query_parameter


class HTTPAPIError(Exception):
    pass


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
        pretty = get_query_parameter(qdata, ['p', 'pretty'], 'no') == 'yes'

        results = None
        m = re.match(r'/export/(event|categ)/(\w+(?:-\w+)*)\.(\w+)/?$', path)
        if m and m.group(3) in ExportInterface.getAllowedFormats():
            dtype, idlist, dformat = m.groups()
            idlist = idlist.split('-')

            expInt = ExportInterface(DBMgr.getInstance())

            tzName = get_query_parameter(qdata, ['tz'], None)

            if dtype == 'categ':
                results = expInt.category(idlist, tzName, qdata)

        if results:
            serializer = Serializer.create(dformat, pretty=pretty, **remove_lists(qdata))
            resp = serializer.getMIMEType(), serializer(results)

    if resp:
        if not from_cache:
            cache.cacheObject(path, qdata_copy, resp)
        mime, result = resp
        req.headers_out['Content-Type'] = mime
        return result
    else:
        # TODO: usage page
        raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND
