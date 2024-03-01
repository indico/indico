# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.notes.util import check_note_revision
from indico.web.util import ExpectedError


@pytest.mark.parametrize(('note_id', 'prev_note_id', 'expected'), (
    (None, None, None),
    (1, 1, None),
))
def test_valid_check_note_revision(note_id, prev_note_id, expected):
    assert check_note_revision(note_id, prev_note_id) == expected


def test_invalid_check_note_revision():
    with pytest.raises(ExpectedError, match="418 I'm a teapot: The note has been modified in the meantime"):
        check_note_revision(2, 1)
