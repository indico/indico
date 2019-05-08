# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from datetime import timedelta

import pytest

from indico.modules.events.contributions.models.contributions import Contribution


@pytest.fixture
def create_contribution(db):
    """Returns a a callable that lets you create a contribution"""

    def _create_contribution(event, title, duration):
        entry = Contribution(event=event, title=title, duration=duration)
        db.session.add(entry)
        db.session.flush()
        return entry

    return _create_contribution


@pytest.fixture
def dummy_contribution(create_contribution, dummy_event):
    return create_contribution(dummy_event, "Dummy Contribution", timedelta(minutes=20))
