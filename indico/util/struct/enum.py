# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from __future__ import absolute_import

import json
from enum import Enum


class IndicoEnum(Enum):
    """Enhanced Enum

    You can use SomeEnum.get('some_name') like you could with a dict.
    """
    @classmethod
    def get(cls, name, default=None):
        try:
            return cls[name]
        except KeyError:
            return default

    @classmethod
    def serialize(cls):
        return json.dumps({x.name: x.value for x in cls})


class TitledEnum(IndicoEnum):
    """Titled Enum

    All members have a `title` property that corresponds to their entry in __titles__
    """
    __titles__ = []

    @property
    def title(self):
        return self.__titles__[self]


class TitledIntEnum(int, TitledEnum):
    pass
