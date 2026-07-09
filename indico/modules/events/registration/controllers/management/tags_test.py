# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events import EventLogRealm
from indico.modules.events.registration.controllers.management.tags import _assign_registration_tags
from indico.modules.events.registration.models.tags import RegistrationTag
from indico.modules.logs import LogKind


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


def test_assign_tags_logs_added(dummy_reg, create_tag):
    tag_a = create_tag('Alpha')
    tag_b = create_tag('Beta')

    _assign_registration_tags([dummy_reg], add={tag_a, tag_b}, remove=set())

    entry = dummy_reg.event.log_entries.one()
    assert entry.realm == EventLogRealm.management
    assert entry.kind == LogKind.positive
    assert entry.module == 'Registration'
    assert dummy_reg.full_name in entry.summary
    assert 'Alpha' in entry.summary
    assert 'Beta' in entry.summary
    assert entry.meta['registration_id'] == dummy_reg.id


def test_assign_tags_logs_removed(db, dummy_reg, create_tag):
    tag_a = create_tag('Alpha')
    dummy_reg.tags.add(tag_a)
    db.session.flush()

    _assign_registration_tags([dummy_reg], add=set(), remove={tag_a})

    entry = dummy_reg.event.log_entries.one()
    assert entry.realm == EventLogRealm.management
    assert entry.kind == LogKind.negative
    assert entry.module == 'Registration'
    assert dummy_reg.full_name in entry.summary
    assert 'Alpha' in entry.summary
    assert entry.meta['registration_id'] == dummy_reg.id


def test_assign_tags_logs_both(db, dummy_reg, create_tag):
    tag_a = create_tag('Alpha')
    tag_b = create_tag('Beta')
    dummy_reg.tags.add(tag_a)
    db.session.flush()

    _assign_registration_tags([dummy_reg], add={tag_b}, remove={tag_a})

    entries = dummy_reg.event.log_entries.all()
    assert len(entries) == 2
    kinds = {e.kind for e in entries}
    assert kinds == {LogKind.positive, LogKind.negative}


def test_assign_tags_no_log_when_nothing_changes(dummy_reg, create_tag):
    tag_a = create_tag('Alpha')
    tag_b = create_tag('Beta')
    # empty changeset
    _assign_registration_tags([dummy_reg], add=set(), remove=set())
    assert not dummy_reg.event.log_entries.has_rows()
    # redundant changes
    dummy_reg.tags = {tag_a}
    _assign_registration_tags([dummy_reg], add={tag_a}, remove=set())
    _assign_registration_tags([dummy_reg], add=set(), remove={tag_b})
    assert not dummy_reg.event.log_entries.has_rows()
    # nonsense change
    _assign_registration_tags([dummy_reg], add={tag_b}, remove={tag_b})
    assert not dummy_reg.event.log_entries.has_rows()
