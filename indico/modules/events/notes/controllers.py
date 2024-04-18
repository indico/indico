# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import jsonify, redirect, request, session
from marshmallow_enum import EnumField
from webargs import fields
from werkzeug.exceptions import Forbidden, NotFound

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.links import LinkType
from indico.core.db.sqlalchemy.util.models import attrs_changed
from indico.modules.events.models.events import EventType
from indico.modules.events.notes import logger
from indico.modules.events.notes.models.notes import EventNote, RenderMode
from indico.modules.events.notes.schemas import CompiledEventNoteSchema, EventNoteSchema
from indico.modules.events.notes.util import can_edit_note, check_note_revision, get_scheduled_notes
from indico.modules.events.util import check_event_locked, get_object_from_args
from indico.modules.logs import EventLogRealm, LogKind
from indico.util.string import sanitize_html
from indico.web.args import use_kwargs
from indico.web.flask.util import url_for
from indico.web.rh import RH, RHProtected


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


class RHApiNote(RHManageNoteBase):
    """Return, edit or delete a note attached to an object inside an event."""

    def _process_GET(self):
        note = EventNote.get_for_linked_object(self.object, preload_event=False)
        if note is None:
            return jsonify()
        return EventNoteSchema().dump(note.current_revision)

    @use_kwargs({
        'render_mode': EnumField(RenderMode, load_default=RenderMode.html),
        'source': fields.String(required=True),
        'revision_id': fields.Integer(),
    })
    def _process_POST(self, render_mode, source, revision_id=None):
        note = EventNote.get_or_create(self.object)
        is_new = note.id is None or note.is_deleted
        is_restored = is_new and note.is_deleted
        check_note_revision(note, revision_id, render_mode, source)
        note.create_revision(render_mode, source, session.user)
        is_changed = attrs_changed(note, 'current_revision')
        db.session.add(note)
        db.session.flush()
        if is_new:
            if is_restored:
                signals.event.notes.note_restored.send(note)
            else:
                signals.event.notes.note_added.send(note)
            logger.info('Note %s created by %s', note, session.user)
            self.event.log(EventLogRealm.participants, LogKind.positive, 'Minutes', 'Added minutes',
                           session.user, data=note.link_event_log_data)
        elif is_changed:
            signals.event.notes.note_modified.send(note)
            logger.info('Note %s modified by %s', note, session.user)
            self.event.log(EventLogRealm.participants, LogKind.change, 'Minutes', 'Updated minutes',
                           session.user, data=note.link_event_log_data)
        return EventNoteSchema().jsonify(note.current_revision)

    def _process_DELETE(self):
        note = EventNote.get_for_linked_object(self.object, preload_event=False)
        current_note_revision = None if note is None else note.current_revision
        if note is not None:
            note.delete(session.user)
            signals.event.notes.note_deleted.send(note)
            logger.info('Note %s deleted by %s', note, session.user)
            self.event.log(EventLogRealm.participants, LogKind.negative, 'Minutes', 'Removed minutes',
                           session.user, data=note.link_event_log_data)
        return EventNoteSchema().jsonify(current_note_revision)


class RHApiCompileNotes(RHManageNoteBase):
    def _process_GET(self):
        notes = get_scheduled_notes(self.event)
        return jsonify(notes=CompiledEventNoteSchema(many=True).dump([n.current_revision for n in notes]))


class RHGotoNote(RH):
    def _get_embed_url(self, note):
        if note.event.type_ == EventType.conference:
            # we have no pretty note pages for conferences
            return None
        elif note.link_type == LinkType.event:
            return url_for('events.display', note.event, note=note.id)
        elif note.link_type == LinkType.session:
            try:
                block = note.session.blocks[0]
            except IndexError:
                return None
            return url_for('events.display', note.event, note=note.id, _anchor=block.slug)
        elif note.link_type in (LinkType.contribution, LinkType.subcontribution):
            return url_for('events.display', note.event, note=note.id, _anchor=note.object.slug)

    def _process(self):
        note = EventNote.get_or_404(request.view_args['note_id'])
        if embed_url := self._get_embed_url(note):
            return redirect(embed_url)
        return redirect(url_for('.view', note))
