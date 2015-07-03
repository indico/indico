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

from flask import redirect, render_template, session
from werkzeug.exceptions import NotFound, Forbidden

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import attrs_changed
from indico.core.errors import NoReportError
from indico.modules.events.logs import EventLogRealm, EventLogKind
from indico.modules.events.notes import logger
from indico.modules.events.notes.forms import NoteForm
from indico.modules.events.notes.util import get_all_notes
from indico.modules.events.notes.models.notes import EventNote, RenderMode
from indico.modules.events.util import get_object_from_args
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_template, jsonify_data
from MaKaC.webinterface.rh.base import RHProtected
from MaKaC.accessControl import AccessWrapper


class RHNoteBase(RHProtected):
    """Base handler for notes attached to an object inside an event"""

    def _checkParams(self):
        self.object_type, self.event, self.object = get_object_from_args()
        if self.object is None:
            raise NotFound


class RHManageNoteBase(RHNoteBase):
    """Base handler for managing notes attached to an object inside an event"""

    def _checkProtection(self):
        RHNoteBase._checkProtection(self)
        if not self._doProcess:
            return
        if self.object_type == 'session' and self.object.canCoordinate(session.avatar):
            return
        if self.object_type == 'contribution' and self.object.canUserSubmit(session.avatar):
            return
        if not self.object.canModify(session.avatar):
            raise Forbidden


class RHEditNote(RHManageNoteBase):
    """Create/edit/delete a note attached to an object inside an event"""

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
        return NoteForm(obj=self._get_defaults(note=note, source=source), linked_object=self.object)

    def _process_form(self, form, **kwargs):
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
                logger.info('Note {} created by {}'.format(note, session.user))
                self.event.log(EventLogRealm.participants, EventLogKind.positive, 'Minutes',
                               'Added minutes to {} {}'.format(self.object_type, self.object.getTitle()), session.user)
            elif is_changed:
                signals.event.notes.note_modified.send(note)
                logger.info('Note {} modified by {}'.format(note, session.user))
                self.event.log(EventLogRealm.participants, EventLogKind.change, 'Minutes',
                               'Updated minutes for {} {}'.format(self.object_type, self.object.getTitle()),
                               session.user)
            return jsonify_data(flash=False)
        return jsonify_template('events/notes/edit_note.html', form=form, object_type=self.object_type,
                                object=self.object, **kwargs)

    def _process_GET(self):
        form = self._make_form()
        return self._process_form(form)

    def _process_POST(self):
        form = self._make_form()
        return self._process_form(form)


class RHCompileNotes(RHEditNote):
    """Handle note edits a note attached to an object inside an event"""

    def _process(self):
        if self.event.note:
            raise NoReportError(_("This event already has a note attached."))
        source = render_template('events/notes/compiled_notes.html', notes=get_all_notes(self.event))
        form = self._make_form(source=source)
        return self._process_form(form, is_compilation=True)


class RHDeleteNote(RHManageNoteBase):
    """Handles deletion of a note attached to an object inside an event"""

    def _process(self):
        note = EventNote.get_for_linked_object(self.object, preload_event=False)
        if note is not None:
            note.delete(session.user)
            signals.event.notes.note_deleted.send(note)
            logger.info('Note {} deleted by {}'.format(note, session.user))
            self.event.log(EventLogRealm.participants, EventLogKind.negative, 'Minutes',
                           'Removed minutes from {} {}'.format(self.object_type, self.object.getTitle()), session.user)
        return redirect(url_for('event.conferenceDisplay', self.event))


class RHViewNote(RHNoteBase):
    """Handles display of a note attached to an object inside an event"""

    def _checkProtection(self):
        RHNoteBase._checkProtection(self)
        if not self.object.canAccess(AccessWrapper(session.avatar)):
            raise Forbidden

    def _process(self):
        note = EventNote.get_for_linked_object(self.object, preload_event=False)
        if not note:
            raise NotFound
        return note.html
