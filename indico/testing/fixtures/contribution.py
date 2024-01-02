# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import timedelta

import pytest

from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.subcontributions import SubContribution


@pytest.fixture
def create_contribution(db):
    """Return a callable that lets you create a contribution."""

    def _create_contribution(event, title, duration=timedelta(minutes=20), **kwargs):
        entry = Contribution(event=event, title=title, duration=duration, **kwargs)
        db.session.add(entry)
        db.session.flush()
        return entry

    return _create_contribution


@pytest.fixture
def dummy_contribution(create_contribution, dummy_event):
    return create_contribution(dummy_event, 'Dummy Contribution', id=420)


@pytest.fixture
def create_subcontribution(db):
    """Return a callable that lets you create a subcontribution."""
    def _create_subcontribution(contribution, title, duration=timedelta(minutes=10), **kwargs):
        entry = SubContribution(contribution=contribution, title=title, duration=duration, **kwargs)
        db.session.add(entry)
        db.session.flush()
        return entry

    return _create_subcontribution


@pytest.fixture
def dummy_subcontribution(dummy_contribution, create_subcontribution):
    """Create a dummy subcontribution."""
    return create_subcontribution(dummy_contribution, 'Dummy SubContribution', id=420)
