# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from functools import wraps

from indico.core.db import db


def no_autoflush(fn):
    """Wrap the decorated function in a no-autoflush block."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        with db.session.no_autoflush:
            return fn(*args, **kwargs)
    return wrapper
