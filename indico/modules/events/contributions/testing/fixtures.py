# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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
def create_contribution(db, dummy_event_new):
    """Returns a a callable that lets you create a contribution"""

    def _create_contribution(title, duration):
        entry = Contribution(event_new=dummy_event_new, title=title, duration=duration)
        db.session.add(entry)
        db.session.flush()
        return entry

    return _create_contribution


@pytest.fixture
def dummy_contribution(create_contribution):
    return create_contribution(title="Dummy Contribution", duration=timedelta(minutes=20))
