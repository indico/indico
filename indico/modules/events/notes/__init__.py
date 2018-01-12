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

from indico.core import signals
from indico.core.logger import Logger


logger = Logger.get('events.notes')


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    from indico.modules.events.notes.models.notes import EventNoteRevision
    EventNoteRevision.find(user_id=source.id).update({EventNoteRevision.user_id: target.id})


@signals.event_management.get_cloners.connect
def _get_attachment_cloner(sender, **kwargs):
    from indico.modules.events.notes.clone import NoteCloner
    return NoteCloner
