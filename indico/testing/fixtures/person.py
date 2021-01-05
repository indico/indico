# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import pytest

from indico.modules.events.models.persons import EventPerson


@pytest.fixture
def create_event_person(db):
    def _create(event, user=None, first_name=None, last_name=None, email=None, affiliation=None, title=None):
        person = EventPerson(event=event,
                             user=user,
                             first_name=first_name or user.first_name,
                             last_name=last_name or user.last_name,
                             email=email or user.email,
                             affiliation=affiliation or user.affiliation,
                             title=title or user.title)
        db.session.add(person)
        db.session.flush()
        return person
    return _create
