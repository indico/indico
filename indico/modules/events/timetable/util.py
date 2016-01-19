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

from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.modules.events.timetable.models.entries import TimetableEntryType


def ensure_timetable_consistency(event, delete=False):
    """Ensure that the timetable of an event is consistent.

    This checks each contribution entry and ensures that it matches
    the session association of the contribution.

    A contribution that has no session assigned, may not be scheduled
    inside a session.  A contribution that has a session assigned may
    only be scheduled inside a session block associated with that
    session, and that session block must match the session block of
    the contribution.

    :param event: The event to check.
    :param delete: Whether to delete inconsistent timetable entries.
                   If False, a `RuntimeError` is raised instead of
                   modifying the timetable.
    :return: boolean indicating if there were any inconsistencies
    """
    query = (event.timetable_entries
             .filter_by(parent_id=None)
             .filter(db.m.TimetableEntry.type != TimetableEntryType.BREAK)
             .options(joinedload('children')))
    inconsistent = set()
    for entry in query:
        if entry.type == TimetableEntryType.CONTRIBUTION:
            # top-level timetable entry for a contribution with no session (block)
            if entry.contribution.session_id is not None or entry.contribution.session_block_id is not None:
                inconsistent.add(entry)
        elif entry.type == TimetableEntryType.SESSION_BLOCK:
            for child in entry.children:
                if child.type != TimetableEntryType.CONTRIBUTION:
                    continue
                # child contribution entries must be associated with the proper session (block)
                if (child.contribution.session_id != entry.session_block.session_id or
                        child.contribution.session_block_id != entry.session_block.id):
                    inconsistent.add(child)
    if not inconsistent:
        return False
    if not delete:
        raise RuntimeError('Found inconsistent timetable entries for event {}: {}'.format(event, inconsistent))
    for entry in inconsistent:
        entry.object.timetable_entry = None
    return True
