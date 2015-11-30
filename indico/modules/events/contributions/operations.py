# This file is part of Indico.# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.logs.models.entries import EventLogRealm, EventLogKind


def create_contribution(event, data):
    contrib = Contribution(event_new=event)
    for key, value in data.iteritems():
        setattr(contrib, key, value)
    db.session.flush()
    event.log(EventLogRealm.management, EventLogKind.positive, 'Contributions',
              'Contribution "{}" has been created'.format(contrib.title), session.user)
    return contrib


def update_contribution(contrib, data):
    for key, value in data.iteritems():
        setattr(contrib, key, value)
    db.session.flush()
    contrib.event_new.log(EventLogRealm.management, EventLogKind.change, 'Contributions',
                          'Contribution "{}" has been updated'.format(contrib.title), session.user)


def delete_contribution(contrib):
    contrib.is_deleted = True
    db.session.flush()
    contrib.event_new.log(EventLogRealm.management, EventLogKind.negative, 'Contributions',
                          'Contribution "{}" has been deleted'.format(contrib.title), session.user)
