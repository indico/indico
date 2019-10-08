# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.marshmallow import mm
from indico.modules.events.models.events import Event


class EventSchema(mm.ModelSchema):
    class Meta:
        model = Event
        fields = ('id', 'title', 'is_locked')


event_schema = EventSchema()
