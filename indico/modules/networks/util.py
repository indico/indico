# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals


def serialize_ip_network_group(group):
    """Serialize group to JSON-like object."""
    return {
        'id': group.id,
        'name': group.name,
        'identifier': 'IPNetworkGroup:{}'.format(group.id),
        '_type': 'IPNetworkGroup'
    }
