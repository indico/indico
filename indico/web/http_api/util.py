# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from werkzeug.exceptions import UnprocessableEntity


def get_query_parameter(queryParams, keys, default=None, integer=False):
    if not isinstance(keys, (list, tuple, set)):
        keys = (keys,)
    for k in keys:
        if k not in queryParams:
            continue
        val = queryParams.pop(k)
        if integer:
            try:
                val = int(val)
            except ValueError:
                raise UnprocessableEntity(f'Expected an integer for {k}')
        return val
    return default
