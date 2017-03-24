# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

import time

from indico.core.config import Config
from indico.legacy.common.fossilize import fossilizes, Fossilizable
from indico.web.http_api.fossils import IHTTPAPIErrorFossil, IHTTPAPIResultFossil


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

    def __init__(self, results, path='', query='', ts=None, complete=True, extra=None):
        if ts is None:
            ts = int(time.time())
        self._results = results
        self._path = path
        self._query = query
        self._ts = ts
        self._complete = complete
        self._extra = extra or {}

    def getTS(self):
        return self._ts

    def getURL(self):
        prefix = Config.getInstance().getBaseURL()
        if self._query:
            return prefix + self._path + '?' + self._query
        return prefix + self._path

    def getCount(self):
        return len(self._results)

    def getResults(self):
        return self._results

    def getComplete(self):
        return self._complete

    def getAdditionalInfo(self):
        return self._extra
