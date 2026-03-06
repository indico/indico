# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import timedelta

import pytest

from indico.modules.events import Event
from indico.modules.events.models.events import EventType
from indico.modules.events.models.labels import EventLabel
from indico.modules.events.registration.models.checks import RegistrationCheckType
from indico.util.date_time import now_utc
from indico.util.string import crc32


# https://github.com/mathiasbynens/small/blob/master/bmp.bmp
DUMMY_BMP_IMAGE = (b'BM\x1e\x00\x00\x00\x00\x00\x00\x00\x1a\x00\x00\x00\x0c\x00'
                   b'\x00\x00\x01\x00\x01\x00\x01\x00\x18\x00\x00\x00\xff\x00')


@pytest.fixture
def create_event(dummy_user, dummy_category, db, dummy_check_type):
    """Return a callable which lets you create dummy events."""

    def _create_event(id_=None, creator=None, creator_has_privileges=False, **kwargs):
        creator = creator or dummy_user
        # we specify `acl_entries` so SA doesn't load it when accessing it for
        # the first time, which would require no_autoflush blocks in some cases
        now = now_utc(exact=False)
        kwargs.setdefault('type_', EventType.meeting)
        kwargs.setdefault('title', f'dummy#{id_}' if id_ is not None else 'dummy')
        kwargs.setdefault('start_dt', now)
        kwargs.setdefault('end_dt', now + timedelta(hours=1))
        kwargs.setdefault('timezone', 'UTC')
        kwargs.setdefault('category', dummy_category)
        kwargs.setdefault('default_check_type_id', dummy_check_type.id)
        event = Event(id=id_, creator=creator, acl_entries=set(), **kwargs)

        if creator_has_privileges:
            event.update_principal(creator, full_access=True)

        db.session.flush()
        return event

    return _create_event


@pytest.fixture
def create_label(db):
    """Return a callable which lets you create dummy labels."""

    def _create_label(title, color='red'):
        label = EventLabel(title=title, color=color)
        db.session.add(label)
        db.session.flush()
        return label

    return _create_label


@pytest.fixture
def dummy_event(create_event):
    """Create a mocked dummy event."""
    return create_event(0)


@pytest.fixture
def dummy_event_logo(dummy_event):
    dummy_event.logo = DUMMY_BMP_IMAGE
    dummy_event.logo_metadata = {
        'hash': crc32(dummy_event.logo),
        'size': len(dummy_event.logo),
        'filename': 'dummy-event-logo.bmp',
        'content_type': 'image/bmp'
    }


@pytest.fixture
def create_registration_check_type(db):
    """Return a callable which lets you create dummy RegistrationCheckTypes."""

    def _create_registration_check_type(title=None, is_system_defined=False):
        check_type = RegistrationCheckType(title=title, is_system_defined=is_system_defined)
        db.session.add(check_type)
        db.session.flush()
        return check_type

    return _create_registration_check_type


@pytest.fixture
def dummy_check_type(create_registration_check_type):
    """Create a mocked dummy RegistrationCheckType."""
    return create_registration_check_type(title='Check type', is_system_defined=True)
