# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import fields

from indico.core.marshmallow import mm
from indico.modules.events.models.persons import EventPerson


class EventPersonSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EventPerson
        fields = ('id', 'identifier', 'email', 'affiliation', 'full_name',
                  'first_name', 'last_name', 'user_identifier')

    full_name = fields.Function(lambda ep: f'{ep.first_name} {ep.last_name}'.strip() or 'Unknown')
    user_identifier = fields.String(attribute='user.identifier')
