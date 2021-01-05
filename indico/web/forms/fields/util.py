# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import absolute_import, unicode_literals


def is_preprocessed_formdata(valuelist):
    if len(valuelist) != 1:
        return False
    value = valuelist[0]
    return isinstance(value, (dict, list))
