# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import fields, post_dump

from indico.core.db import db
from indico.core.marshmallow import mm
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.rooms import Room
from indico.util.i18n import _
from indico.util.marshmallow import ModelField


class LocationDataSchema(mm.Schema):
    venue = ModelField(Location, allow_none=True, data_key='venue_id')
    room = ModelField(Room, allow_none=True, data_key='room_id')
    venue_name = fields.String()
    room_name = fields.String()
    address = fields.String()
    inheriting = fields.Boolean()


class LocationParentSchema(mm.Schema):
    location_data = fields.Nested(LocationDataSchema)
    title = fields.String()

    @post_dump(pass_original=True)
    def _add_type(self, data, orig, **kwargs):
        match orig:
            case db.m.Contribution():
                data['type'] = _('Contribution')
            case db.m.Break():
                data['type'] = _('Break')
            case db.m.SessionBlock():
                data['type'] = _('Block')
            case db.m.Session():
                data['type'] = _('Session')
            case db.m.Event():
                data['type'] = _('Event')
            case _:
                raise TypeError(f'Unexpected parent type {type(orig)}')
        return data
