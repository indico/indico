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
