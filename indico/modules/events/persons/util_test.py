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

from indico.modules.events.persons.util import create_event_person, get_event_person, get_event_person_for_user


def test_get_person_for_user(db, dummy_event, dummy_user):
    person = get_event_person_for_user(dummy_event, dummy_user)
    # EventPerson created from scratch
    assert person.id is None
    assert person.user == dummy_user
    db.session.add(person)
    db.session.flush()
    person = get_event_person_for_user(dummy_event, dummy_user)
    # Already existing EventPerson
    assert person.id is not None
    assert person.user == dummy_user


def test_create_event_person(db, dummy_event):
    data = {
        'email': 'test@acme.com',
        'firstName': 'John',
        'familyName': 'Doe',
        'affiliation': 'ACME Inc.'
    }
    person = create_event_person(dummy_event, **data)
    assert person.event == dummy_event
    assert person.email == 'test@acme.com'
    assert person.full_name == 'John Doe'
    assert person.affiliation == 'ACME Inc.'


def test_get_event_person(db, dummy_event, dummy_user):
    data = {
        'email': 'test@acme.com',
        'firstName': 'John',
        'familyName': 'Doe',
        'affiliation': 'ACME Inc.'
    }
    person_1 = get_event_person(dummy_event, data)
    # Person doesn't exist in the DB
    assert person_1.id is None
    # User neither
    assert person_1.user is None
    # save in the DB for later
    db.session.add(person_1)
    db.session.flush()

    data = {
        'email': '1337@example.com',
        'firstName': 'Sea',
        'familyName': 'Pig',
        'affiliation': 'ACME Inc.'
    }
    person_2 = get_event_person(dummy_event, data)
    # Person not in the DB either
    assert person_2.id is None
    # User exists, however (matched by e-mail)
    assert person_2.user == dummy_user
    assert person_2.full_name == 'Guinea Pig'

    db.session.add(person_2)
    db.session.flush()
    person = get_event_person(dummy_event, data)
    # Retrieved person should now be in the DB
    assert person.id == person_2.id

    # User for whom there is already an EventPerson in this event
    data = {
        'email': 'test@acme.com',
        'firstName': 'JOHN',
        'familyName': 'DOE',
        'affiliation': 'ACME'
    }
    person_3 = get_event_person(dummy_event, data)
    # We should get the first person
    assert person_3.id == person_1.id
    assert person_3.user is None
    assert person_3.full_name == 'John Doe'

    data = {
        'firstName': 'Foo',
        'familyName': 'Bar'
    }
    person_4 = get_event_person(dummy_event, data)
    # We should get a new person
    assert person_4.id is None
    assert person_4.user is None
    assert person_4.email == ''
    assert person_4.full_name == 'Foo Bar'


def test_get_event_person_edit(db, dummy_event, dummy_user):
    data = {
        'email': 'test@acme.com',
        'firstName': 'John',
        'familyName': 'Doe',
        'affiliation': 'ACME Inc.'
    }
    person_1 = get_event_person(dummy_event, dict(data, _type='Avatar', id=dummy_user.id))
    assert person_1.id is None
    assert person_1.user == dummy_user
    db.session.add(person_1)
    db.session.flush()

    person_2 = get_event_person(dummy_event, dict(data, _type='EventPerson', id=person_1.id))
    assert person_2 == person_1

    person_3 = get_event_person(dummy_event, dict(data, _type='PersonLink', personId=person_1.id))
    assert person_3 == person_1

    with pytest.raises(ValueError):
        get_event_person(dummy_event, dict(data, _type='UnsupportedPersonType'))
