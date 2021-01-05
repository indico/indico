# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core import signals
from indico.util.signals import named_objects_from_signal
from indico.web.fields.base import BaseField


__all__ = ('BaseField', 'get_field_definitions')


def get_field_definitions(for_):
    """Get a dict containing all field definitions.

    :param for_: The identifier/object passed to the `get_fields`
                 signal to identify which fields to get.
    """
    return named_objects_from_signal(signals.get_fields.send(for_), plugin_attr='plugin')
