# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.models.persons import EventPerson


@pytest.fixture
def create_event_person(db):
    """Return a callable which lets you create event persons."""
    def _create(event, user=None, first_name=None, last_name=None, email=None, affiliation=None, title=None):
        person = EventPerson(event=event,
                             user=user,
                             first_name=first_name or user.first_name,
                             last_name=last_name or user.last_name,
                             email=email or user.email,
                             affiliation=affiliation or user.affiliation,
                             title=title or user._title)
        db.session.add(person)
        db.session.flush()
        return person
    return _create


@pytest.fixture
def dummy_event_person(dummy_event, dummy_user, create_event_person):
    """Create a dummy event person."""
    return create_event_person(dummy_event, dummy_user)
