# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.notes.models.notes import EventNote, RenderMode
from indico.modules.events.notes.util import check_note_revision
from indico.web.util import ExpectedError


@pytest.fixture
def note(db, dummy_event):
    note = EventNote(object=dummy_event)
    db.session.expunge(note)
    return note


def test_valid_revision(db, note, dummy_user):
    previous = note.create_revision(RenderMode.html, 'second', dummy_user)
    db.session.add(note)
    db.session.flush()
    check_note_revision(note, previous.id, RenderMode.html, '<h1>foo</h1>')


def test_invalid_revision(db, note, dummy_user):
    current = note.create_revision(RenderMode.html, 'first', dummy_user)
    previous = note.create_revision(RenderMode.html, 'second', dummy_user)
    db.session.add(note)
    db.session.flush()
    with pytest.raises(ExpectedError) as exc_info:
        check_note_revision(note, current.id, RenderMode.html, '<h1>foo</h1>')
    assert exc_info.value.data['conflict']['id'] == previous.id


def test_empty_revision(db, note, dummy_user):
    previous = note.create_revision(RenderMode.html, '', dummy_user)
    db.session.add(note)
    db.session.flush()
    check_note_revision(note, previous.id, RenderMode.html, '<h1>foo</h1>')
