# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import timedelta

import pytest

from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.timetable.models.breaks import Break
from indico.modules.events.timetable.models.entries import TimetableEntry, TimetableEntryType
from indico.util.date_time import now_utc


@pytest.fixture
def create_timetable_entry(db):
    """Return a callable that lets you create a timetable entry."""

    def _create_timetable_entry(event, obj, start_dt, parent=None):
        if isinstance(obj, SessionBlock):
            entry_type = TimetableEntryType.SESSION_BLOCK
        elif isinstance(obj, Contribution):
            entry_type = TimetableEntryType.CONTRIBUTION
        elif isinstance(obj, Break):
            entry_type = TimetableEntryType.BREAK
        else:
            raise NotImplementedError
        entry = TimetableEntry(event=event, object=obj, start_dt=start_dt, parent=parent, type=entry_type)
        db.session.add(entry)
        db.session.flush()
        return entry

    return _create_timetable_entry


@pytest.fixture
def create_break(db, create_timetable_entry):
    """Return a callable that lets you create a break."""

    def _create_break(event, title, duration, start_dt, **kwargs):
        break_ = Break(title=title, duration=duration, **kwargs)
        db.session.add(break_)
        db.session.flush()
        create_timetable_entry(event, break_, start_dt)
        return break_

    return _create_break


@pytest.fixture
def dummy_break(create_break, dummy_event):
    return create_break(dummy_event, 'Dummy break', timedelta(minutes=5), now_utc(False))
