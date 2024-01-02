# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

def get_query_parameter(queryParams, keys, default=None, integer=False):
    if not isinstance(keys, (list, tuple, set)):
        keys = (keys,)
    for k in keys:
        if k not in queryParams:
            continue
        val = queryParams.pop(k)
        if integer:
            val = int(val)
        return val
    return default
