# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from marshmallow import fields

from indico.core.marshmallow import mm
from indico.modules.events.models.events import Event
from indico.modules.events.models.principals import EventPrincipal
from indico.util.marshmallow import PrincipalPermissionList


class EventPermissionsSchema(mm.Schema):
    acl_entries = PrincipalPermissionList(EventPrincipal, all_permissions=True)


class EventDetailsSchema(mm.ModelSchema):
    class Meta:
        model = Event
        fields = ('id', 'category_chain', 'title', 'start_dt', 'end_dt')

    category_chain = fields.List(fields.String(), attribute='category.chain_titles')


event_permissions_schema = EventPermissionsSchema()
