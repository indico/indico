# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

# The code in here is taken almost verbatim from `django.utils.encoding`,
# which is licensed under the three-clause BSD license and is originally
# available on the following URL:
# https://github.com/django/django/blob/425b26092f/django/utils/encoding.py
# Credits of the original code go to the Django Software Foundation
# and their contributors.

import datetime
from decimal import Decimal
from types import NoneType


DEFAULT_CHARSET = 'utf-8'


class DjangoUnicodeDecodeError(UnicodeDecodeError):
    def __str__(self):
        return '%s. You passed in %r (%s)' % (
            super().__str__(),
            self.object,
            type(self.object),
        )


_PROTECTED_TYPES = (
    NoneType,
    int,
    float,
    Decimal,
    datetime.datetime,
    datetime.date,
    datetime.time,
)


def is_protected_type(obj):
    """Determine if the object instance is of a protected type.

    Objects of protected types are preserved as-is when passed to
    force_str(strings_only=True).
    """
    return isinstance(obj, _PROTECTED_TYPES)


def force_str(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Similar to smart_str(), except that lazy instances are resolved to
    strings, rather than kept as lazy objects.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    # Handle the common case first for performance reasons.
    if issubclass(type(s), str):
        return s
    if strings_only and is_protected_type(s):
        return s
    try:
        if isinstance(s, bytes):
            s = str(s, encoding, errors)
        else:
            s = str(s)
    except UnicodeDecodeError as e:
        raise DjangoUnicodeDecodeError(*e.args) from None
    return s


def punycode(domain):
    """Return the Punycode of the given domain if it's non-ASCII."""
    return domain.encode('idna').decode('ascii')
