# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import fields

from indico.core.marshmallow import mm
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.models.sessions import Session


class SessionBlockSchema(mm.SQLAlchemyAutoSchema):
    room_name_verbose = fields.Function(lambda obj: obj.get_room_name(full=False, verbose=True))

    class Meta:
        model = SessionBlock
        fields = ('id', 'title', 'code', 'start_dt', 'end_dt', 'duration', 'room_name', 'room_name_verbose')


class BasicSessionSchema(mm.SQLAlchemyAutoSchema):
    blocks = fields.List(fields.Nested(SessionBlockSchema))

    class Meta:
        model = Session
        fields = ('id', 'title', 'friendly_id', 'code', 'blocks')
