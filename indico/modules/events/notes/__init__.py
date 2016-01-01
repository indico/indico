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

from indico.core import signals
from indico.core.db import db
from indico.core.logger import Logger
from indico.util.i18n import _
from MaKaC.conference import EventCloner


logger = Logger.get('events.notes')


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    from indico.modules.events.notes.models.notes import EventNoteRevision
    EventNoteRevision.find(user_id=source.id).update({EventNoteRevision.user_id: target.id})


class NoteCloner(EventCloner):
    def find_notes(self):
        return self.event.as_event.notes.filter_by(is_deleted=False)

    def get_options(self):
        enabled = bool(self.find_notes().count())
        return {'notes': (_("Minutes"), enabled, False)}

    def clone(self, new_event, options):
        from indico.modules.events.notes.models.notes import EventNote
        if 'notes' not in options:
            return
        for old_note in self.find_notes():
            revision = old_note.current_revision
            new_note = EventNote(link_type=old_note.link_type,
                                 event_id=new_event.id,
                                 session_id=old_note.session_id,
                                 contribution_id=old_note.contribution_id,
                                 subcontribution_id=old_note.subcontribution_id)
            new_note.create_revision(render_mode=revision.render_mode,
                                     source=revision.source,
                                     user=revision.user)
            db.session.add(new_note)
            db.session.flush()
            logger.info('Added note during event cloning: {}'.format(new_note))


@signals.event_management.clone.connect
def _get_note_cloner(event, **kwargs):
    return NoteCloner(event)


@signals.event.session_deleted.connect
@signals.event.contribution_deleted.connect
@signals.event.subcontribution_deleted.connect
def _delete_note(obj, **kwargs):
    if obj.note:
        obj.note.is_deleted = True
