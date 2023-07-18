# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import sys
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

    # Python 3.11 up to 3.11.4 switched from by-value to by-name serialization of enums,
    # causing the tests for event exporting (to yaml) to fail. This has been reverted in
    # the 3.11 branch (https://github.com/python/cpython/pull/105348), so likely 3.11.5
    # will no longer need the fix below.
    # Once released, we can possibly use package metadata to explicitly exclude older 3.11
    # releases or just keep the code below around forever
    if (3, 11, 0) <= sys.version_info[:3] <= (3, 11, 4):
        def __reduce_ex__(self, proto):
            return self.__class__, (self._value_,)

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
    pass


class RichEnum(_RichEnumMixin, IndicoEnum):
    """An Enum that stores extra information per entry."""


class RichIntEnum(_IndicoEnumMixin, _RichEnumMixin, int, ReprEnum):
    pass


class RichStrEnum(_IndicoEnumMixin, _RichEnumMixin, str, ReprEnum):
    pass
