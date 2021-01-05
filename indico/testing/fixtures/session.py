# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from datetime import timedelta

import pytest

from indico.modules.events.sessions.models.sessions import Session


@pytest.fixture
def create_session(db):
    """Return a callable that lets you create a session."""

    def _create_session(event, title, duration):
        entry = Session(event=event, title=title)
        db.session.add(entry)
        db.session.flush()
        return entry

    return _create_session


@pytest.fixture
def dummy_session(create_session, dummy_event):
    return create_session(dummy_event, 'Dummy session', timedelta(minutes=20))
