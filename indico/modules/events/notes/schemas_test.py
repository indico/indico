# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

def test_sanitize_note_html():
    from indico.modules.events.notes.schemas import CompiledEventNoteSchema, EventNoteSchema
    note = {'html': '<img onerror="evil" src="x">'}
    assert EventNoteSchema().dump(note)['html'] == '<img src="x">'
    assert CompiledEventNoteSchema().dump(note)['html'] == '<img src="x">'
