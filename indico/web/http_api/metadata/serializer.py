# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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



class Serializer(object):

    schemaless = True
    encapsulate = True

    registry = {}

    def __init__(self, query_params, pretty=False, **kwargs):
        self.pretty = pretty
        self._query_params = query_params
        self._fileName = None
        self._lastModified = None
        self._extra_args = kwargs

    @classmethod
    def register(cls, tag, serializer):
        cls.registry[tag] = serializer

    @classmethod
    def getAllFormats(cls):
        return list(cls.registry)

    @classmethod
    def create(cls, dformat, query_params=None, **kwargs):
        """
        A serializer factory
        """

        query_params = query_params or {}

        serializer = cls.registry.get(dformat)

        if serializer:
            return serializer(query_params, **kwargs)
        else:
            raise Exception("Serializer for '%s' does not exist!" % dformat)

    def getMIMEType(self):
        return self._mime

    def set_headers(self, response):
        response.content_type = self.getMIMEType()

    def __call__(self, obj, *args, **kwargs):
        self._obj = obj
        self._data = self._execute(obj, *args, **kwargs)
        return self._data


from indico.web.http_api.metadata.json import JSONSerializer
from indico.web.http_api.metadata.xml import XMLSerializer
