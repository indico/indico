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

import itertools

from indico.web.flask.util import url_for
from MaKaC.conference import Conference, Contribution, SessionSlot
from MaKaC.schedule import BreakTimeSchEntry


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


def get_nested_notes(obj):
    """Gets all notes linked to the object and its nested objects.

    In case of :class:`Conference`, nested objects have to be scheduled.

    :param obj: A :class:`Conference`, :class:`SessionSlot`,
                :class:`Contribution` or :class:`SubContribution` object.
    """
    notes = [obj.note] if obj.note else []
    nested_objects = []
    if isinstance(obj, Conference):
        nested_objects = [e.getOwner() for e in obj.getSchedule().getEntries() if not isinstance(e, BreakTimeSchEntry)]
    if isinstance(obj, SessionSlot):
        nested_objects = obj.getContributionList()
    elif isinstance(obj, Contribution):
        nested_objects = obj.getSubContributionList()
    return itertools.chain(notes, *map(get_nested_notes, nested_objects))
