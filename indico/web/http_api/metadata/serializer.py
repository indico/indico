# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.


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

    def get_response_content_type(self):
        return self.getMIMEType()

    def __call__(self, obj, *args, **kwargs):
        self._obj = obj
        self._data = self._execute(obj, *args, **kwargs)
        return self._data


from indico.web.http_api.metadata.json import JSONSerializer  # noqa: F401,E402
from indico.web.http_api.metadata.xml import XMLSerializer  # noqa: F401,E402
