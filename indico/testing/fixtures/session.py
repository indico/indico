# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import timedelta

import pytest

from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.models.sessions import Session
from indico.util.date_time import now_utc


@pytest.fixture
def create_session(db):
    """Return a callable that lets you create a session."""

    def _create_session(event, title):
        entry = Session(event=event, title=title)
        db.session.add(entry)
        db.session.flush()
        return entry

    return _create_session


@pytest.fixture
def create_session_block(db, create_timetable_entry):
    """Return a callable that lets you create a session block."""

    def _create_session_block(session, title, duration, start_dt):
        block = SessionBlock(session=session, title=title, duration=duration)
        db.session.add(block)
        db.session.flush()
        create_timetable_entry(session.event, block, start_dt)
        return block

    return _create_session_block


@pytest.fixture
def dummy_session(create_session, dummy_event):
    return create_session(dummy_event, 'Dummy session')


@pytest.fixture
def dummy_session_block(create_session_block, dummy_session):
    return create_session_block(dummy_session, 'Dummy block', timedelta(minutes=20), now_utc())
