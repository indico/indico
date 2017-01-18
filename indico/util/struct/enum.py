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

from __future__ import absolute_import

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
        return {x.name: x.value for x in cls}


class RichEnum(IndicoEnum):
    """An Enum that stores extra information per entry."""
    __titles__ = []
    __css_classes__ = []

    @property
    def title(self):
        return self.__titles__[self] if self.__titles__ else None

    @property
    def css_class(self):
        return self.__css_classes__[self] if self.__css_classes__ else None


class RichIntEnum(int, RichEnum):
    pass
