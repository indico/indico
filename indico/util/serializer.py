# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from enum import Enum

from indico.core.errors import IndicoError
from indico.core.logger import Logger


class Serializer(object):
    __public__ = []

    def to_serializable(self, attr='__public__', converters=None):
        serializable = {}
        if converters is None:
            converters = {}
        for k in getattr(self, attr):
            try:
                if isinstance(k, tuple):
                    k, name = k
                else:
                    k, name = k, k

                v = getattr(self, k)
                if callable(v):  # to make it generic, we can get rid of it by properties
                    v = v()
                if isinstance(v, Serializer):
                    v = v.to_serializable()
                elif isinstance(v, list):
                    v = [e.to_serializable() for e in v]
                elif isinstance(v, dict):
                    v = dict((k, vv.to_serializable() if isinstance(vv, Serializer) else vv)
                             for k, vv in v.iteritems())
                elif isinstance(v, Enum):
                    v = v.name
                if type(v) in converters:
                    v = converters[type(v)](v)
                serializable[name] = v
            except Exception:
                msg = 'Could not retrieve {}.{}.'.format(self.__class__.__name__, k)
                Logger.get('Serializer{}'.format(self.__class__.__name__)).exception(msg)
                raise IndicoError(msg)
        return serializable
