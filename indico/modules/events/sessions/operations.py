# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from flask import session

from indico.core.db import db
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.logs.models.entries import EventLogRealm, EventLogKind


def create_session(event, data=None):
    """Create a new session with the information passed in the `data` argument"""
    event_session = Session(event_new=event)
    event_session.populate_from_dict(data or {})
    db.session.flush()
    event.log(EventLogRealm.management, EventLogKind.positive, 'Sessions',
              'Session "{}" has been created'.format(event_session.title), session.user)
    return event_session
