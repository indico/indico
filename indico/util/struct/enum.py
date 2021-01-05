# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import absolute_import

from enum import Enum


class IndicoEnum(Enum):
    """Enhanced Enum.

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
