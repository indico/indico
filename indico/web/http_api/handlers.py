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
from indico.web.wsgi import webinterface_handler_config as apache

# indico legacy imports
from MaKaC.common import DBMgr


class HTTPAPIError(Exception):
    pass


def get_query_parameter(qdata, keys, default=None, integer=False):
    if type(keys) != list:
        keys = list(keys)
    for k in keys:
        paramlist = qdata.get(k)
        if paramlist:
            if len(paramlist) == 1:
                val = paramlist[0]
                if integer:
                    val = int(val)
                return val
            else:
                raise Exception("duplicate argument' %s'!" % k)
    return None


def handler(req, **params):
    path, query = req.URLFields['PATH_INFO'], req.URLFields['QUERY_STRING']

    m = re.match(r'/export/(event|categ)/(\w+(?:-\w+)*)\.(json|xml|rss|ical|html)/?',
                 path)

    if m:
        dtype, idlist, dformat = m.groups()
        idlist = idlist.split('-')
        qdata = dict(parse_qs(query))
        orderBy = get_query_parameter(qdata, ['o', 'order'])
        descending = get_query_parameter(qdata, ['c', 'descending'], False)
        detail = get_query_parameter(qdata, ['d', 'detail'], 'events')

        expInt = ExportInterface(DBMgr.getInstance())

        if dtype == 'categ':
            fromDT = get_query_parameter(qdata, ['f', 'from'])
            toDT = get_query_parameter(qdata, ['t', 'to'])
            location = get_query_parameter(qdata, ['l', 'location'])
            limit = get_query_parameter(qdata, ['n', 'limit'], integer=True)

            return expInt.category(idlist, dformat, fromDT, toDT, location,
                                   limit, orderBy, descending, detail)
    else:
        # TODO: usage page
        raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND
