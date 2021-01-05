# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core import signals
from indico.util.signals import named_objects_from_signal


def get_request_definitions():
    """Return a dict of request definitions."""
    return named_objects_from_signal(signals.plugin.get_event_request_definitions.send(), plugin_attr='plugin')


def is_request_manager(user):
    """Check if the user manages any request types."""
    if not user:
        return False
    return any(def_.can_be_managed(user) for def_ in get_request_definitions().itervalues())
