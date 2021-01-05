# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals


def serialize_event_role(role, legacy=True):
    """Serialize role to JSON-like object."""
    if legacy:
        return {
            'id': role.id,
            'name': role.name,
            'code': role.code,
            'color': role.color,
            'identifier': 'EventRole:{}'.format(role.id),
            '_type': 'EventRole'
        }
    else:
        return {
            'id': role.id,
            'name': role.name,
            'identifier': 'EventRole:{}'.format(role.id),
        }
