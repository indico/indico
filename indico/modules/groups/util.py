# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals


def serialize_group(group):
    """Serialize group to JSON-like object."""
    return {
        'id': group.id if group.is_local else group.name,
        'name': group.name,
        'provider': group.provider,
        'provider_title': group.provider_title if not group.is_local else None,
        'identifier': group.identifier,
        '_type': 'LocalGroup' if group.is_local else 'MultipassGroup',
        'isGroup': True
    }
