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

from flask import session, request, redirect, jsonify
from werkzeug.exceptions import NotFound, Forbidden

from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import attrs_changed
from indico.modules.events.logs import EventLogRealm, EventLogKind
from indico.modules.events.notes import logger
from indico.modules.events.notes.forms import NoteForm
from indico.modules.events.notes.models.notes import EventNote, RenderMode
from indico.web.forms.base import FormDefaults
from MaKaC.conference import ConferenceHolder
from MaKaC.webinterface.pages.base import WPJinjaMixin
from MaKaC.webinterface.rh.base import RHProtected


class RHEditNote(RHProtected):
    """Create/edit a note attached to an object inside an event"""

    def _checkParams(self):
        self.object = None
        self.object_type = request.view_args['object_type']
        self.event = ConferenceHolder().getById(request.view_args['confId'], True)
        if self.event is None:
            raise NotFound
        if self.object_type == 'event':
            self.object = self.event
        elif self.object_type == 'session':
            self.object = self.event.getSessionById(request.view_args['sessionId'])
        elif self.object_type == 'contribution':
            self.object = self.event.getContributionById(request.view_args['contribId'])
        elif self.object_type == 'subcontribution':
            contrib = self.event.getContributionById(request.view_args['contribId'])
            if contrib is not None:
                self.object = contrib.getSubContributionById(request.view_args['subContId'])
        if self.object is None:
            raise NotFound

    def _checkProtection(self):
        RHProtected._checkProtection(self)
        if not self._doProcess:
            return
        if self.object_type == 'session' and self.object.canCoordinate(session.avatar):
            return
        if self.object_type == 'contribution' and self.object.canUserSubmit(session.avatar):
            return
        if not self.object.canModify(session.avatar):
            raise Forbidden

    def _get_defaults(self, note):
        if note:
            return FormDefaults(note.current_revision)
        else:
            # TODO: set default render mode once it can be selected
            return FormDefaults()

    def _process_form(self):
        note = EventNote.get_for_linked_object(self.object, preload_event=False)
        form = NoteForm(obj=self._get_defaults(note))
        if form.validate_on_submit():
            note = EventNote.get_or_create(self.object)
            is_new = note.id is None
            # TODO: get render mode from form data once it can be selected
            note.create_revision(RenderMode.html, form.source.data, session.user)
            is_changed = attrs_changed(note, 'current_revision')
            db.session.add(note)
            db.session.flush()
            if is_new:
                logger.info('Note {} created by {}'.format(note, session.user))
                self.event.log(EventLogRealm.participants, EventLogKind.positive, 'Minutes',
                               'Added minutes to {} {}'.format(self.object_type, self.object.getTitle()), session.user)
            elif is_changed:
                logger.info('Note {} modified by {}'.format(note, session.user))
                self.event.log(EventLogRealm.participants, EventLogKind.change, 'Minutes',
                               'Updated minutes for {} {}'.format(self.object_type, self.object.getTitle()),
                               session.user)
            return jsonify(success=True)
        return WPJinjaMixin.render_template('events/notes/edit_note.html', form=form, note=note,
                                            object_type=self.object_type, object=self.object)

    def _process_GET(self):
        return self._process_form()

    def _process_POST(self):
        return self._process_form()

    def _process_DELETE(self):
        note = EventNote.get_for_linked_object(self.object, preload_event=False)
        if note is not None:
            note.delete(session.user)
            logger.info('Note {} deleted by {}'.format(note, session.user))
            self.event.log(EventLogRealm.participants, EventLogKind.negative, 'Minutes',
                           'Removed minutes from {} {}'.format(self.object_type, self.object.getTitle()), session.user)
        return jsonify(success=True)
