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
HTTP API - Response objects
"""

# python stdlib imports
import time

# indico imports
from indico.web.http_api.fossils import IHTTPAPIErrorFossil, IHTTPAPIResultFossil

# indico legacy imports
from MaKaC.common.Configuration import Config
from MaKaC.common.fossilize import fossilizes, fossilize, Fossilizable

class HTTPAPIError(Exception, Fossilizable):
    fossilizes(IHTTPAPIErrorFossil)

    def __init__(self, message, code=None):
        self.message = message
        self.code = code

    def getMessage(self):
        return self.message

    def getCode(self):
        return self.code


class HTTPAPIResult(Fossilizable):
    fossilizes(IHTTPAPIResultFossil)

    def __init__(self, results, path='', query='', ts=None, complete=True):
        if ts is None:
            ts = int(time.time())
        self._results = results
        self._path = path
        self._query = query
        self._ts = ts
        self._complete = complete

    def getTS(self):
        return self._ts

    def getURL(self):
        prefix = Config.getInstance().getBaseSecureURL()
        if self._query:
            return prefix + self._path + '?' + self._query
        return prefix + self._path

    def getCount(self):
        return len(self._results)

    def getResults(self):
        return self._results

    def getComplete(self):
        return self._complete
