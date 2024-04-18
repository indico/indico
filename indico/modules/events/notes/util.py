# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.orm import joinedload, noload

from indico.core.db import db
from indico.modules.events.settings import autolinker_settings
from indico.modules.events.timetable.models.entries import TimetableEntry, TimetableEntryType
from indico.util.string import AutoLinkExtension, HTMLLinker, render_markdown
from indico.web.flask.util import url_for
from indico.web.util import ExpectedError


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
    """Get all notes of scheduled items inside an event."""
    def _sort_note_by(note):
        obj = note.object
        if hasattr(obj, 'start_dt'):
            return obj.start_dt, 0
        else:
            return obj.contribution.start_dt, obj.position

    tt_entries = (event.timetable_entries
                  .filter(TimetableEntry.type != TimetableEntryType.BREAK)
                  .options(joinedload('session_block').joinedload('contributions').joinedload('subcontributions'))
                  .options(joinedload('contribution').joinedload('subcontributions'))
                  .options(noload('break_'))
                  .all())
    # build a list of all the objects we need notes for. that way we can query
    # all notes in a single go afterwards instead of making the already-huge
    # timetable query even bigger.
    objects = set()
    for entry in tt_entries:
        objects.add(entry.object)
        if entry.type == TimetableEntryType.CONTRIBUTION:
            objects.update(sc for sc in entry.object.subcontributions if not sc.is_deleted)
        elif entry.type == TimetableEntryType.SESSION_BLOCK:
            for contrib in entry.object.contributions:
                objects.add(contrib)
                objects.update(sc for sc in contrib.subcontributions if not sc.is_deleted)
    notes = [x for x in event.all_notes.filter_by(is_deleted=False) if x.object in objects]
    return sorted(notes, key=_sort_note_by)


def can_edit_note(obj, user):
    """Check if a user can edit the object's note."""
    if not user:
        return False
    if obj.can_manage(user):
        return True
    if isinstance(obj, db.m.Event) and obj.can_manage(user, 'submit'):
        return True
    if isinstance(obj, db.m.Contribution) and obj.can_manage(user, 'submit'):
        return True
    if isinstance(obj, db.m.SubContribution):
        subcontrib_speakers_can_submit = obj.contribution.event.subcontrib_speakers_can_submit
        if subcontrib_speakers_can_submit and any(speaker.person.user == user for speaker in obj.speakers):
            return True
        return can_edit_note(obj.contribution, user)
    return False


def check_note_revision(note, previous_revision_id, render_mode, source):
    """Compare revision IDs to check if the note has been modified."""
    from indico.modules.events.notes.schemas import EventNoteSchema
    if previous_revision_id is None:
        if note.current_revision_id and not note.is_deleted:
            conflicting_note = EventNoteSchema().dump(note.current_revision)
            raise ExpectedError('The note has been modified in the meantime', conflict=conflicting_note,
                                html=render_note(source, render_mode))
        return

    if note.current_revision_id != previous_revision_id:
        conflicting_note = EventNoteSchema().dump(note.current_revision)
        raise ExpectedError('The note has been modified in the meantime', conflict=conflicting_note,
                            html=render_note(source, render_mode))


def render_note(source, mode):
    """Render a note from source using the specified render mode."""
    from indico.core.db.sqlalchemy.descriptions import RenderMode
    autolinker_rules = autolinker_settings.get('rules')
    if mode == RenderMode.html:
        return HTMLLinker(autolinker_rules).process(source)
    if mode == RenderMode.markdown:
        return render_markdown(source, extensions=('nl2br', AutoLinkExtension(autolinker_rules)))
    raise ValueError(f'Invalid render mode: {mode}')
