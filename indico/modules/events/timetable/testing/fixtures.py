# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import pytest

from indico.modules.events.timetable.models.entries import TimetableEntry


@pytest.fixture
def create_entry(db):
    """Return a a callable which lets you create timetable."""

    def _create_entry(obj, start_dt):
        entry = TimetableEntry(event=obj.event, object=obj, start_dt=start_dt)
        db.session.add(entry)
        db.session.flush()
        return entry

    return _create_entry
