# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import fields

from indico.core.marshmallow import mm
from indico.modules.networks import IPNetworkGroup


class IPNetworkGroupSchema(mm.Schema):
    class Meta:
        model = IPNetworkGroup
        fields = ('id', '_type', 'name', 'identifier')

    _type = fields.Constant('IPNetworkGroup', dump_only=True)
