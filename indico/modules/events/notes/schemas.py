# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.marshmallow import fields, mm
from indico.modules.events.notes.models.notes import EventNoteRevision


class EventNoteSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EventNoteRevision
        fields = ('source', 'render_mode')


class CompiledEventNoteSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EventNoteRevision
        fields = ('source', 'html', 'render_mode', 'object_title')

    object_title = fields.String(attribute='note.object.title')
