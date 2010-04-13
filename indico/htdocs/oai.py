# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

import socket
from datetime import datetime

import MaKaC.export.oai2 as oai2
from MaKaC.common import info
from MaKaC.common import DBMgr
from MaKaC.common.logger import Logger

from mod_python import apache

def __request(req, params, private=False):
    start = datetime.now()
    DBMgr.getInstance().startRequest()
    a=oai2.OAIResponse(req.hostname, req.uri, private)
    response = a.oaiResponseMaker(params)

    DBMgr.getInstance().abort()
    DBMgr.getInstance().endRequest()

    stop = datetime.now()
    tsec = (stop-start).seconds
    msec = (stop-start).microseconds
    min = int(tsec/60)
    sec = tsec-min*60

    Logger.get('oai/interface').debug("from: %s request: %s responseTime: %s\n" %(req.connection.remote_ip, req.unparsed_uri, "%d:%d:%d"%(min, sec, msec)  ))
 
    req.content_type = "text/xml"   # set content type
    return response

# Public interface - accessible to everybody
def index(req, **params):
    return __request(req, params)

# Private interface - protected events (search engine)
def private(req, **params):

    # load allowed IP address list from DB
    DBMgr.getInstance().startRequest()
    
    minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
    ipList = minfo.getOAIPrivateHarvesterList()[:]

    useProxy = minfo.useProxy()
    
    DBMgr.getInstance().endRequest()


    # Check that we are using HTTPS
    # TODO: uncomment as soon as Invenio supports HTTPS
    if True: #req.is_https():
        remoteHost = req.get_remote_host(apache.REMOTE_NOLOOKUP)

        # if we're using a proxy and we trust it (i.e. load balancer),
        # use X-Forward-For instead
        if useProxy:
            xff = req.headers_in.get("X-Forwarded-For",remoteHost).split(", ")[-1]
            remoteHost = socket.gethostbyname(xff)

        # Check remote host (is it in the "allowed harvesters" table?
        if remoteHost in ipList:
            # make the request
            return __request(req, params, private=True)
        else:
            # 403 Forbidden
            req.content_type = 'text/plain'
            req.status = apache.HTTP_FORBIDDEN
            return "You (%s) are not allowed to access this service" % remoteHost

    # No HTTPS - 403 Forbidden
    else:
        req.content_type = 'text/plain'
        req.status = apache.HTTP_FORBIDDEN
        return "The Private Gateway only works over HTTPS"
