# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import redirect, render_template, session
from werkzeug.exceptions import Forbidden, NotFound

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import attrs_changed
from indico.modules.events.logs import EventLogKind, EventLogRealm
from indico.modules.events.notes import logger
from indico.modules.events.notes.forms import NoteForm
from indico.modules.events.notes.models.notes import EventNote, RenderMode
from indico.modules.events.notes.util import can_edit_note, get_scheduled_notes
from indico.modules.events.util import check_event_locked, get_object_from_args
from indico.util.string import sanitize_html
from indico.web.forms.base import FormDefaults
from indico.web.rh import RHProtected
from indico.web.util import jsonify_template


class RHNoteBase(RHProtected):
    """Base handler for notes attached to an object inside an event."""

    def _process_args(self):
        self.object_type, self.event, self.object = get_object_from_args()
        if self.object is None:
            raise NotFound


class RHManageNoteBase(RHNoteBase):
    """Base handler for managing notes attached to an object inside an event."""

    def _check_access(self):
        RHNoteBase._check_access(self)
        if not can_edit_note(self.object, session.user):
            raise Forbidden
        check_event_locked(self, self.event)


class RHEditNote(RHManageNoteBase):
    """Create/edit a note attached to an object inside an event."""

    def _get_defaults(self, note=None, source=None):
        if source:
            return FormDefaults(source=source)
        elif note:
            return FormDefaults(note.current_revision)
        else:
            # TODO: set default render mode once it can be selected
            return FormDefaults()

    def _make_form(self, source=None):
        note = None
        if not source:
            note = EventNote.get_for_linked_object(self.object, preload_event=False)
        return NoteForm(obj=self._get_defaults(note=note, source=source))

    def _process_form(self, form, **kwargs):
        saved = False
        if form.validate_on_submit():
            note = EventNote.get_or_create(self.object)
            is_new = note.id is None or note.is_deleted
            # TODO: get render mode from form data once it can be selected
            note.create_revision(RenderMode.html, form.source.data, session.user)
            is_changed = attrs_changed(note, 'current_revision')
            db.session.add(note)
            db.session.flush()
            if is_new:
                signals.event.notes.note_added.send(note)
                logger.info('Note %s created by %s', note, session.user)
                self.event.log(EventLogRealm.participants, EventLogKind.positive, 'Minutes', 'Added minutes',
                               session.user, data=note.link_event_log_data)
            elif is_changed:
                signals.event.notes.note_modified.send(note)
                logger.info('Note %s modified by %s', note, session.user)
                self.event.log(EventLogRealm.participants, EventLogKind.change, 'Minutes', 'Updated minutes',
                               session.user, data=note.link_event_log_data)
            saved = is_new or is_changed
        return jsonify_template('events/notes/edit_note.html', form=form, object_type=self.object_type,
                                object=self.object, saved=saved, **kwargs)

    def _process(self):
        form = self._make_form()
        return self._process_form(form)


class RHCompileNotes(RHEditNote):
    """Handle note edits a note attached to an object inside an event."""

    def _process(self):
        source = render_template('events/notes/compiled_notes.html', notes=get_scheduled_notes(self.event))
        form = self._make_form(source=source)
        return self._process_form(form, is_compilation=True)


class RHDeleteNote(RHManageNoteBase):
    """Handle deletion of a note attached to an object inside an event."""

    def _process(self):
        note = EventNote.get_for_linked_object(self.object, preload_event=False)
        if note is not None:
            note.delete(session.user)
            signals.event.notes.note_deleted.send(note)
            logger.info('Note %s deleted by %s', note, session.user)
            self.event.log(EventLogRealm.participants, EventLogKind.negative, 'Minutes', 'Removed minutes',
                           session.user, data=note.link_event_log_data)
        return redirect(self.event.url)


class RHViewNote(RHNoteBase):
    """Handle display of a note attached to an object inside an event."""

    def _check_access(self):
        if not self.object.can_access(session.user):
            raise Forbidden

    def _process(self):
        note = EventNote.get_for_linked_object(self.object, preload_event=False)
        if not note:
            raise NotFound
        return sanitize_html(note.html)
