# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

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
