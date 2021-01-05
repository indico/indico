# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import timedelta

import pytest

from indico.modules.events import Event
from indico.modules.events.models.events import EventType
from indico.util.date_time import now_utc


@pytest.fixture
def create_event(dummy_user, dummy_category, db):
    """Return a callable which lets you create dummy events."""

    def _create_event(id_=None, **kwargs):
        # we specify `acl_entries` so SA doesn't load it when accessing it for
        # the first time, which would require no_autoflush blocks in some cases
        now = now_utc(exact=False)
        kwargs.setdefault('type_', EventType.meeting)
        kwargs.setdefault('title', u'dummy#{}'.format(id_) if id_ is not None else u'dummy')
        kwargs.setdefault('start_dt', now)
        kwargs.setdefault('end_dt', now + timedelta(hours=1))
        kwargs.setdefault('timezone', 'UTC')
        kwargs.setdefault('category', dummy_category)
        event = Event(id=id_, creator=dummy_user, acl_entries=set(), **kwargs)
        db.session.flush()
        return event

    return _create_event


@pytest.fixture
def dummy_event(create_event):
    """Create a mocked dummy event."""
    return create_event(0)
