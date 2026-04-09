# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from flask import session

from indico.modules.events import EventLogRealm
from indico.modules.events.registration.controllers.management.tags import _assign_registration_tags
from indico.modules.events.registration.models.tags import RegistrationTag
from indico.modules.logs import LogKind
from indico.modules.logs.models.entries import EventLogEntry


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


@pytest.fixture
def create_tag(db, dummy_event):
    """Return a callable that lets you create a registration tag."""
    def _create_tag(title, color='#ff0000'):
        tag = RegistrationTag(event=dummy_event, title=title, color=color)
        db.session.add(tag)
        db.session.flush()
        return tag
    return _create_tag


@pytest.mark.usefixtures('request_context')
def test_assign_tags_logs_added(db, dummy_reg, dummy_user, create_tag):
    session.set_session_user(dummy_user)
    tag_a = create_tag('Alpha')
    tag_b = create_tag('Beta')

    _assign_registration_tags([dummy_reg], add={tag_a, tag_b}, remove=set())

    entries = EventLogEntry.query.filter_by(event=dummy_reg.event).all()
    assert len(entries) == 1
    entry = entries[0]
    assert entry.realm == EventLogRealm.management
    assert entry.kind == LogKind.positive
    assert entry.module == 'Tags'
    assert dummy_reg.full_name in entry.summary
    assert 'Alpha' in entry.summary
    assert 'Beta' in entry.summary
    assert entry.meta['registration_id'] == dummy_reg.id


@pytest.mark.usefixtures('request_context')
def test_assign_tags_logs_removed(db, dummy_reg, dummy_user, create_tag):
    session.set_session_user(dummy_user)
    tag_a = create_tag('Alpha')
    dummy_reg.tags.add(tag_a)
    db.session.flush()

    _assign_registration_tags([dummy_reg], add=set(), remove={tag_a})

    entries = EventLogEntry.query.filter_by(event=dummy_reg.event).all()
    assert len(entries) == 1
    entry = entries[0]
    assert entry.realm == EventLogRealm.management
    assert entry.kind == LogKind.negative
    assert entry.module == 'Tags'
    assert dummy_reg.full_name in entry.summary
    assert 'Alpha' in entry.summary
    assert entry.meta['registration_id'] == dummy_reg.id


@pytest.mark.usefixtures('request_context')
def test_assign_tags_logs_both(db, dummy_reg, dummy_user, create_tag):
    session.set_session_user(dummy_user)
    tag_a = create_tag('Alpha')
    tag_b = create_tag('Beta')
    dummy_reg.tags.add(tag_a)
    db.session.flush()

    _assign_registration_tags([dummy_reg], add={tag_b}, remove={tag_a})

    entries = EventLogEntry.query.filter_by(event=dummy_reg.event).order_by(EventLogEntry.id).all()
    assert len(entries) == 2
    kinds = {e.kind for e in entries}
    assert kinds == {LogKind.positive, LogKind.negative}


@pytest.mark.usefixtures('request_context')
def test_assign_tags_no_log_when_nothing_changes(db, dummy_reg, dummy_user):
    session.set_session_user(dummy_user)

    _assign_registration_tags([dummy_reg], add=set(), remove=set())

    assert EventLogEntry.query.filter_by(event=dummy_reg.event).count() == 0
