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

import pytest

from indico.modules.events.timetable.models.entries import TimetableEntry


@pytest.fixture
def create_entry(db, dummy_event):
    """Returns a a callable which lets you create timetable"""

    def _create_entry(obj, start_dt):
        entry = TimetableEntry(event=dummy_event, object=obj, start_dt=start_dt)
        db.session.add(entry)
        db.session.flush()
        return entry

    return _create_entry
