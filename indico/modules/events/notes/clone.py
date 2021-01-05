# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.core.db.sqlalchemy.links import LinkType
from indico.modules.events.cloning import EventCloner
from indico.modules.events.notes.models.notes import EventNote
from indico.util.i18n import _


class NoteCloner(EventCloner):
    name = 'notes'
    friendly_name = _('Minutes')
    uses = {'sessions', 'contributions'}

    @property
    def is_available(self):
        return self._has_content(self.old_event)

    def has_conflicts(self, target_event):
        return self._has_content(target_event)

    def run(self, new_event, cloners, shared_data, event_exists=False):
        self._clone_nested_notes = False
        self._session_map = self._contrib_map = self._subcontrib_map = None
        if cloners >= {'sessions', 'contributions'}:
            self._clone_nested_notes = True
            self._session_map = shared_data['sessions']['session_map']
            self._contrib_map = shared_data['contributions']['contrib_map']
            self._subcontrib_map = shared_data['contributions']['subcontrib_map']
        with db.session.no_autoflush:
            self._clone_notes(new_event)
        db.session.flush()

    def _has_content(self, event):
        return event.all_notes.filter_by(is_deleted=False).has_rows()

    def _query_notes(self):
        return (self.old_event.all_notes
                .filter_by(is_deleted=False)
                .filter(EventNote.link_type.in_([LinkType.session, LinkType.contribution, LinkType.subcontribution]))
                .options(joinedload('session'),
                         joinedload('contribution'),
                         joinedload('subcontribution'),
                         joinedload('current_revision').joinedload('user')))

    def _clone_notes(self, new_event):
        # event note
        if self.old_event.note:
            self._clone_note(self.old_event.note, new_event)
        # session/contrib/subcontrib notes
        if self._clone_nested_notes:
            mapping = {LinkType.session: self._session_map,
                       LinkType.contribution: self._contrib_map,
                       LinkType.subcontribution: self._subcontrib_map}
            for old_note in self._query_notes():
                obj = old_note.object
                if obj.is_deleted or (isinstance(obj, db.m.SubContribution) and obj.contribution.is_deleted):
                    continue
                self._clone_note(old_note, mapping[old_note.link_type][obj])

    def _clone_note(self, old_note, new_object):
        revision = old_note.current_revision
        new_object.note = EventNote()
        new_object.note.create_revision(render_mode=revision.render_mode, source=revision.source, user=revision.user)
