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

from flask import session

from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.contributions import logger
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.logs.models.entries import EventLogRealm, EventLogKind


def _ensure_consistency(contrib):
    """Unschedule contribution if not consistent with timetable

    A contribution that has no session assigned, may not be scheduled
    inside a session.  A contribution that has a session assigned may
    only be scheduled inside a session block associated with that
    session, and that session block must match the session block of
    the contribution.

    :return: A dict containing the data needed to
    """
    entry = contrib.timetable_entry
    if entry is None:
        return False
    if entry.parent_id is None and (contrib.session is not None or contrib.session_block is not None):
        # Top-level entry but we have a session/block set
        contrib.timetable_entry = None
        return True
    elif entry.parent_id is not None:
        parent = entry.parent
        # Nested entry but no or a different session/block set
        if parent.session_block.session != contrib.session or parent.session_block != contrib.session_block:
            contrib.timetable_entry = None
            return True


def create_contribution(event, data):
    contrib = Contribution(event_new=event)
    for person in data.pop('people', []):
        contrib.person_links.append(person)
    contrib.populate_from_dict(data)
    db.session.flush()
    logger.info('Contribution %s created by %s', contrib, session.user)
    contrib.event_new.log(EventLogRealm.management, EventLogKind.positive, 'Contributions',
                          'Contribution "{}" has been created'.format(contrib.title), session.user)
    return contrib


@no_autoflush
def update_contribution(contrib, data):
    """Update a contribution

    :param contrib: The `Contribution` to update
    :param data: A dict containing the data to update
    :return: A dictionary containing information related to the
             update.  `unscheduled` will be true if the modification
             resulted in the contribution being unscheduled.  In this
             case `undo_unschedule` contains the necessary data to
             re-schedule it (undoing the session change causing it to
             be unscheduled)
    """
    rv = {'unscheduled': False, 'undo_unschedule': None}
    current_session_block = contrib.session_block
    contrib.person_links = []
    for person in data.pop('people', []):
        contrib.person_links.append(person)
    contrib.populate_from_dict(data)
    if 'session' in data:
        timetable_entry = contrib.timetable_entry
        if timetable_entry is not None and _ensure_consistency(contrib):
            rv['unscheduled'] = True
            rv['undo_unschedule'] = {'start_dt': timetable_entry.start_dt.isoformat(),
                                     'contribution_id': contrib.id,
                                     'session_block_id': current_session_block.id if current_session_block else None,
                                     'force': True}
    db.session.flush()
    logger.info('Contribution %s updated by %s', contrib, session.user)
    contrib.event_new.log(EventLogRealm.management, EventLogKind.change, 'Contributions',
                          'Contribution "{}" has been updated'.format(contrib.title), session.user)
    return rv


def delete_contribution(contrib):
    contrib.is_deleted = True
    contrib.timetable_entry = None
    db.session.flush()
    logger.info('Contribution %s deleted by %s', contrib, session.user)
    contrib.event_new.log(EventLogRealm.management, EventLogKind.negative, 'Contributions',
                          'Contribution "{}" has been deleted'.format(contrib.title), session.user)
