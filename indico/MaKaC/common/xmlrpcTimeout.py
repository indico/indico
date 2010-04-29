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
import sys

import xmlrpclib
from MaKaC.common.httpTimeout import HTTPWithTimeout, HTTPSWithTimeout

class TransportWithTimeout(xmlrpclib.Transport):
        
    def setTimeout(self, timeout):
        self._timeout = timeout

    def make_connection(self, host):
        return HTTPWithTimeout(host, timeout = self._timeout)
    
class SafeTransportWithTimeout(xmlrpclib.SafeTransport):
    
    def setTimeout(self, timeout):
        self._timeout = timeout

    def make_connection(self, host):
        return HTTPSWithTimeout(host, timeout = self._timeout)
    
def getServerWithTimeout(uri, transport=None, encoding=None, verbose=0,
                         allow_none=0, use_datetime=0, timeout = None):
    
    if uri.startswith("https://"):
        transport = SafeTransportWithTimeout()
    else:
        transport = TransportWithTimeout()
    transport.setTimeout(timeout)
    
    if sys.version_info[0] == 2:
        if sys.version_info[1] < 5: #python 2.4. example version_info: version_info = (2,4,4,'final',0)
            return xmlrpclib.ServerProxy(uri, transport, encoding, verbose, allow_none)
        else:
            return xmlrpclib.ServerProxy(uri, transport, encoding, verbose, allow_none, use_datetime)
    else:
        raise Exception("This code will probably need fixing with Python 3")
