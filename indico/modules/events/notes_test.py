# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from unittest.mock import Mock

import pytest

from indico.modules.events.notes.util import check_note_revision
from indico.web.util import ExpectedError


def create_note(current_revision_id=None, is_deleted=False, current_revision=None):
    note = Mock()
    note.current_revision_id = current_revision_id
    note.is_deleted = is_deleted
    note.current_revision = current_revision
    return note


def test_unmodified_new_note():
    # Test that a note is not modified when the current_revision_id is None (new note)
    note = create_note()
    previous_revision_id = None
    assert check_note_revision(note, previous_revision_id) is None


def test_unmodified_existing_note():
    # Test that a note is not modified when the current_revision_id is the same as the previous_revision_id
    note = create_note(current_revision_id=1)
    previous_revision_id = 1
    assert check_note_revision(note, previous_revision_id) is None


def test_note_modified():
    # Test that a note is modified when the current_revision_id is different from the previous_revision_id
    note = create_note(current_revision_id=1)
    previous_revision_id = 2
    with pytest.raises(ExpectedError):
        check_note_revision(note, previous_revision_id)


def test_note_deleted():
    # Test that a note is modified when the note is deleted
    note = create_note(current_revision_id=1, is_deleted=True)
    previous_revision_id = 1
    assert check_note_revision(note, previous_revision_id) is None


def test_note_deleted_modified():
    # Test that a note is modified when the note is deleted and the previous_revision_id is different
    # from the current_revision_id
    note = create_note(current_revision_id=1, is_deleted=True)
    previous_revision_id = 2
    with pytest.raises(ExpectedError):
        check_note_revision(note, previous_revision_id)
