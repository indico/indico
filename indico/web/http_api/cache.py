# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002-2011 CERN.
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
from MaKaC.common.cache import MultiLevelCacheEntry, MultiLevelCache
import datetime
import hashlib
import time
import os

"""
HTTP API - Cache
"""

class RequestCacheEntry(MultiLevelCacheEntry):
    @classmethod
    def create(cls, content):
        entry = cls()
        entry.setContent(content)
        entry._ts = int(time.time())
        return entry

    def getTS(self):
        return self._ts

class RequestCache(MultiLevelCache):
    _entryFactory = RequestCacheEntry

    def __init__(self, ttl=600):
        super(RequestCache, self).__init__('http_api')
        self._ttl = ttl

    def _generateFileName(self, entry, version):
        return 'req.%s' % version

    def _generatePath(self, entry):
        return ['requests']

    def cacheObject(self, key, obj):
        key = hashlib.sha256(key).hexdigest()
        return super(RequestCache, self).cacheObject(key, obj)

    def loadObject(self, key):
        key = hashlib.sha256(key).hexdigest()
        return super(RequestCache, self).loadObject(key)

    def isDirty(self, path, object):
        creationTime = datetime.datetime(*time.localtime(os.path.getmtime(path))[:6])
        return datetime.datetime.now() - creationTime > datetime.timedelta(seconds=self._ttl)
