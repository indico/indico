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

from datetime import timedelta

import pytest

from indico.modules.events import Event
from indico.modules.events.models.events import EventType
from indico.util.date_time import now_utc


@pytest.fixture
def create_event(dummy_user, dummy_category, db):
    """Returns a callable which lets you create dummy events"""

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
    """Creates a mocked dummy event"""
    return create_event(0)
