# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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

from suds.cache import Cache
from MaKaC.common.cache import GenericCache

class SudsCache(Cache):
    _instance = None

    @classmethod
    def getInstance(cls, duration=None):
        if cls._instance is None:
            cls._instance = SudsCache(duration)
        return cls._instance

    def __init__(self, duration=None):
        self._cache = GenericCache("SudsCache")
        if duration is None:
            duration = 24 * 3600 # we put as default 1 day cache
        self._duration = duration

    def get(self, key):
        self._cache.get(key)

    def put(self, key, val):
        self._cache.set(key, val, self._duration)

    def purge(self, key):
        self._cache.delete(key)
