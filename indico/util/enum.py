# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from enum import Enum


try:
    from enum import ReprEnum
except ImportError:  # python<3.11
    ReprEnum = Enum


class _IndicoEnumMixin:
    @classmethod
    def get(cls, name, default=None):
        try:
            return cls[name]
        except KeyError:
            return default

    @classmethod
    def serialize(cls):
        # XXX is this still used anywhere?!
        return {x.name: x.value for x in cls}


class _RichEnumMixin:
    __titles__ = []
    __css_classes__ = []

    @property
    def title(self):
        return self.__titles__[self] if self.__titles__ else None

    @property
    def css_class(self):
        return self.__css_classes__[self] if self.__css_classes__ else None


class IndicoEnum(_IndicoEnumMixin, Enum):
    """Enhanced Enum.

    You can use SomeEnum.get('some_name') like you could with a dict.
    """


class IndicoIntEnum(_IndicoEnumMixin, int, ReprEnum):
    pass


class IndicoStrEnum(_IndicoEnumMixin, str, ReprEnum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()


class RichEnum(_RichEnumMixin, IndicoEnum):
    """An Enum that stores extra information per entry."""


class RichIntEnum(_IndicoEnumMixin, _RichEnumMixin, int, ReprEnum):
    pass


class RichStrEnum(_IndicoEnumMixin, _RichEnumMixin, str, ReprEnum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()
