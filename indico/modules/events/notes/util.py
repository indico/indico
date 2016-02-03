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

from sqlalchemy.orm import joinedload, defaultload

from indico.core.db import db
from indico.modules.events.timetable.models.entries import TimetableEntry, TimetableEntryType
from indico.web.flask.util import url_for


def build_note_api_data(note):
    if note is None:
        return {}
    return {'html': note.html,
            'url': url_for('event_notes.view', note, _external=True),
            'modified_dt': note.current_revision.created_dt.isoformat(),
            'user': note.current_revision.user.id}


def build_note_legacy_api_data(note):
    if note is None:
        return {}
    data = {'_deprecated': True,
            '_fossil': 'localFileMetadata',
            '_type': 'LocalFile',
            'id': 'minutes',
            'name': 'minutes',
            'fileName': 'minutes.txt',
            'url': url_for('event_notes.view', note, _external=True)}
    return {'_deprecated': True,
            '_fossil': 'materialMetadata',
            '_type': 'Minutes',
            'id': 'minutes',
            'resources': [data],
            'title': 'Minutes'}


def get_scheduled_notes(event):
    """Gets all notes of scheduled items inside an event"""
    tt_entries = (event.timetable_entries
                  .filter(TimetableEntry.parent_id.is_(None),
                          TimetableEntry.type != TimetableEntryType.BREAK)
                  .options(joinedload('children'))
                  .options(joinedload('session_block').joinedload('contributions').joinedload('subcontributions'))
                  .options(joinedload('contribution').joinedload('subcontributions'))
                  .all())
    # build a list of all the objects we need notes for. that way we can query
    # all notes in a single go afterwards instead of making the already-huge
    # timetable query even bigger.
    objects = []
    for entry in tt_entries:
        objects.append(entry.object)
        if entry.type == TimetableEntryType.CONTRIBUTION:
            objects.extend(sc for sc in entry.object.subcontributions if not sc.is_deleted)
        elif entry.type == TimetableEntryType.SESSION_BLOCK:
            for contrib in entry.object.contributions:
                objects.append(contrib)
                objects.extend(sc for sc in contrib.subcontributions if not sc.is_deleted)
    used = set(objects)
    notes = [x for x in event.all_notes.filter_by(is_deleted=False) if x.object in used]
    positions = {obj: i for i, obj in enumerate(objects)}
    return sorted(notes, key=lambda x: positions[x.object])


def can_edit_note(obj, user):
    """Checks if a user can edit the object's note"""
    if not user:
        return False
    if obj.can_manage(user):
        return True
    if isinstance(obj, db.m.Event) and obj.can_manage(user, 'submit'):
        return True
    if isinstance(obj, db.m.Session) and obj.can_manage(user, 'coordinate'):
        return True
    if isinstance(obj, db.m.Contribution) and obj.can_manage(user, 'submit'):
        return True
    if isinstance(obj, db.m.SubContribution):
        return can_edit_note(obj.contribution, user)
    return False
