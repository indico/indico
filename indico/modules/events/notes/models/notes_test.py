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

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from indico.modules.events.notes.models.notes import EventNote, EventNoteRevision, RenderMode


@pytest.fixture
def note(db, dummy_event):
    note = EventNote(object=dummy_event)
    db.session.expunge(note)  # keep it out of the SA session (linking it to the event adds it)
    return note


@pytest.mark.parametrize('deleted', (True, False))
def test_create_revision_previously_deleted(db, note, dummy_user, deleted):
    note.is_deleted = deleted
    note.create_revision(RenderMode.html, 'revision', dummy_user)
    assert not note.is_deleted


def test_revisions(db, note, dummy_user):
    rev1 = note.create_revision(RenderMode.html, 'first', dummy_user)
    db.session.add(note)
    db.session.flush()
    assert rev1 == note.current_revision
    assert note.current_revision.html == note.html == 'first'
    assert set(note.revisions) == {rev1}
    rev2 = note.create_revision(RenderMode.html, 'second', dummy_user)
    db.session.flush()
    assert rev2 == note.current_revision
    assert note.current_revision.html == note.html == 'second'
    assert set(note.revisions) == {rev2, rev1}  # order_by is only applied when loading so just check the contents here


def test_change_current_revision(db, note, dummy_user):
    rev1 = note.create_revision(RenderMode.html, 'first', dummy_user)
    rev2 = note.create_revision(RenderMode.html, 'second', dummy_user)
    assert note.current_revision == rev2
    db.session.flush()
    note.current_revision = rev1
    db.session.flush()
    assert note.current_revision.html == note.html == 'first'
    assert set(note.revisions) == {rev2, rev1}


def test_clear_current_revision(note, dummy_user):
    note.create_revision(RenderMode.html, 'first', dummy_user)
    with pytest.raises(ValueError):
        note.current_revision = None


def test_delete_current_revision(db, note, dummy_user):
    note.create_revision(RenderMode.html, 'first', dummy_user)
    rev = note.create_revision(RenderMode.html, 'second', dummy_user)
    db.session.add(note)
    db.session.flush()
    note.revisions.remove(rev)
    with pytest.raises(IntegrityError):
        db.session.flush()


def test_create_same_revision(db, create_user, note, dummy_user):
    user = create_user(123)
    note.create_revision(RenderMode.html, 'test', dummy_user)
    note.create_revision(RenderMode.html, 'test', user)
    db.session.add(note)
    db.session.flush()
    assert len(note.revisions) == 1
    assert note.current_revision.user == dummy_user


def test_delete_other_revision(db, note, dummy_user):
    rev1 = note.create_revision(RenderMode.html, 'first', dummy_user)
    rev2 = note.create_revision(RenderMode.html, 'second', dummy_user)
    db.session.add(note)
    db.session.flush()
    note.revisions.remove(rev1)
    db.session.flush()
    assert set(note.revisions) == {rev2}
    assert EventNoteRevision.query.count() == 1


def test_modify_old_revision_source(db, note, dummy_user):
    rev1 = note.create_revision(RenderMode.html, 'first', dummy_user)
    rev2 = note.create_revision(RenderMode.html, 'second', dummy_user)
    db.session.add(note)
    db.session.flush()
    rev1.source = 'rewritten history'
    assert note.html == rev2.html == 'second'


def test_modify_current_revision_source(db, note, dummy_user):
    note.create_revision(RenderMode.html, 'first', dummy_user)
    rev = note.create_revision(RenderMode.html, 'second', dummy_user)
    db.session.add(note)
    db.session.flush()
    note.current_revision.source = 'rewritten history'
    assert note.html == rev.html == 'rewritten history'


def test_render_html(note, dummy_user):
    note.create_revision(RenderMode.html, '<strong>test</strong>', dummy_user)
    assert note.html == note.current_revision.html == '<strong>test</strong>'


def test_render_markdown(note, dummy_user):
    note.create_revision(RenderMode.markdown, '**test**\n*foo*', dummy_user)
    assert note.html == note.current_revision.html == '<p><strong>test</strong><br>\n<em>foo</em></p>'


def test_get_for_linked_object(note, dummy_user, create_event):
    note.create_revision(RenderMode.html, 'test', dummy_user)
    assert EventNote.get_for_linked_object(note.object) == note
    assert EventNote.get_for_linked_object(create_event(123)) is None


@pytest.mark.parametrize('preload', (True, False))
def test_get_for_linked_object_preload(note, dummy_user, count_queries, preload):
    note.create_revision(RenderMode.html, 'test', dummy_user)
    assert EventNote.get_for_linked_object(note.object, preload_event=preload)
    with count_queries() as cnt:
        EventNote.get_for_linked_object(note.object)
    assert (cnt() == 0) == preload


def test_get_for_linked_object_deleted(note, dummy_user):
    note.create_revision(RenderMode.html, 'test', dummy_user)
    note.is_deleted = True
    assert EventNote.get_for_linked_object(note.object) is None


def test_get_or_create(db, dummy_user, dummy_event, create_event):
    note = EventNote.get_or_create(dummy_event)
    assert note is not None
    assert not inspect(note).persistent  # new object
    note.create_revision(RenderMode.html, 'test', dummy_user)
    note.is_deleted = True
    db.session.flush()
    # get deleted one
    assert EventNote.get_or_create(dummy_event) == note
    assert inspect(note).persistent
    note.is_deleted = False
    db.session.flush()
    # same if it's not deleted
    assert EventNote.get_or_create(dummy_event) == note
    assert inspect(note).persistent
    # other event should create a new one
    other = EventNote.get_or_create(create_event(123))
    other.create_revision(RenderMode.html, 'test', dummy_user)
    assert other != note
    assert not inspect(other).persistent


def test_delete(note, dummy_user):
    note.create_revision(RenderMode.html, 'test', dummy_user)
    note.delete(dummy_user)
    assert len(note.revisions) == 2
    assert note.html == ''
    assert note.is_deleted
