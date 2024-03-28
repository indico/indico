# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.marshmallow import fields, mm
from indico.modules.events.notes.models.notes import EventNoteRevision


class EventNoteSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EventNoteRevision
        fields = ('id', 'created_dt', 'source', 'html', 'render_mode', 'note_author')

    note_author = fields.String(attribute='user.full_name')


class CompiledEventNoteSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EventNoteRevision
        fields = ('source', 'html', 'render_mode', 'object_title')

    object_title = fields.String(attribute='note.object.title')
