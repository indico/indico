# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime
from io import BytesIO

import pytest

from indico.core.db import db
from indico.core.errors import UserValueError
from indico.modules.events.models.persons import EventPerson
from indico.modules.events.registration.models.invitations import RegistrationInvitation
from indico.modules.events.registration.util import (create_registration, get_event_regforms_registrations,
                                                     get_registered_event_persons, import_invitations_from_csv,
                                                     import_registrations_from_csv, import_user_records_from_csv)


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


def test_import_users(dummy_regform):
    csv = b'\n'.join([b'John,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,jdoe@example.com',
                      b'Jane,Smith,ACME Inc.,CEO,,jane@example.com',
                      b'Billy Bob,Doe,,,,1337@example.COM'])

    columns = ['first_name', 'last_name', 'affiliation', 'position', 'phone', 'email']
    users = import_user_records_from_csv(BytesIO(csv), columns)
    assert len(users) == 3

    assert users[0] == {
        'first_name': 'John',
        'last_name': 'Doe',
        'affiliation': 'ACME Inc.',
        'position': 'Regional Manager',
        'phone': '+1-202-555-0140',
        'email': 'jdoe@example.com',
    }

    assert users[1] == {
        'first_name': 'Jane',
        'last_name': 'Smith',
        'affiliation': 'ACME Inc.',
        'position': 'CEO',
        'phone': '',
        'email': 'jane@example.com',
    }

    assert users[2] == {
        'first_name': 'Billy Bob',
        'last_name': 'Doe',
        'affiliation': '',
        'position': '',
        'phone': '',
        'email': '1337@example.com',
    }


def test_import_users_error(create_user):
    columns = ['first_name', 'last_name', 'affiliation', 'position', 'phone', 'email']
    user = create_user(123, email='test1@example.com')
    user.secondary_emails.add('test2@example.com')

    # missing column
    csv = b'\n'.join([b'John,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,jdoe@example.com',
                      b'Buggy,Entry,ACME Inc.,CEO,'])

    with pytest.raises(UserValueError) as e:
        import_user_records_from_csv(BytesIO(csv), columns)
    assert 'malformed' in str(e.value)
    assert 'Row 2' in str(e.value)

    # missing e-mail
    csv = b'\n'.join([b'Bill,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,bdoe@example.com',
                      b'Buggy,Entry,ACME Inc.,CEO,,'])

    with pytest.raises(UserValueError) as e:
        import_user_records_from_csv(BytesIO(csv), columns)
    assert 'missing e-mail' in str(e.value)
    assert 'Row 2' in str(e.value)

    # bad e-mail
    csv = b'\n'.join([b'Bill,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,bdoe@example.com',
                      b'Buggy,Entry,ACME Inc.,CEO,,not-an-email'])

    with pytest.raises(UserValueError) as e:
        import_user_records_from_csv(BytesIO(csv), columns)
    assert 'invalid e-mail' in str(e.value)
    assert 'Row 2' in str(e.value)

    # duplicate e-mail
    csv = b'\n'.join([b'Bill,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,bdoe@example.com',
                      b'Bob,Doe,ACME Inc.,Boss,,bdoe@example.com'])

    with pytest.raises(UserValueError) as e:
        import_user_records_from_csv(BytesIO(csv), columns)
    assert 'email address is not unique' in str(e.value)
    assert 'Row 2' in str(e.value)

    # duplicate user
    csv = b'\n'.join([b'Big,Boss,ACME Inc.,Supreme Leader,+1-202-555-1337,test1@example.com',
                      b'Little,Boss,ACME Inc.,Wannabe Leader,+1-202-555-1338,test2@EXAMPLE.com'])

    with pytest.raises(UserValueError) as e:
        import_user_records_from_csv(BytesIO(csv), columns)
    assert 'Row 2: email address belongs to the same user as in row 1' in str(e.value)

    # missing first name
    csv = b'\n'.join([b'Ray,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,rdoe@example.com',
                      b',Buggy,ACME Inc.,CEO,,buggy@example.com'])

    with pytest.raises(UserValueError) as e:
        import_user_records_from_csv(BytesIO(csv), columns)
    assert 'missing first' in str(e.value)
    assert 'Row 2' in str(e.value)


def test_import_registrations(dummy_regform, dummy_user):
    csv = b'\n'.join([b'John,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,jdoe@example.com',
                      b'Jane,Smith,ACME Inc.,CEO,,jane@example.com',
                      b'Billy Bob,Doe,,,,1337@example.COM'])
    registrations = import_registrations_from_csv(dummy_regform, BytesIO(csv))
    assert len(registrations) == 3

    assert registrations[0].full_name == 'John Doe'
    assert registrations[0].user is None
    data = registrations[0].get_personal_data()
    assert data['affiliation'] == 'ACME Inc.'
    assert data['email'] == 'jdoe@example.com'
    assert data['position'] == 'Regional Manager'
    assert data['phone'] == '+1-202-555-0140'

    assert registrations[1].full_name == 'Jane Smith'
    assert registrations[1].user is None
    data = registrations[1].get_personal_data()
    assert data['affiliation'] == 'ACME Inc.'
    assert data['email'] == 'jane@example.com'
    assert data['position'] == 'CEO'
    assert 'phone' not in data

    assert registrations[2].full_name == 'Billy Bob Doe'
    assert registrations[2].user == dummy_user
    data = registrations[2].get_personal_data()
    assert 'affiliation' not in data
    assert data['email'] == '1337@example.com'
    assert 'position' not in data
    assert 'phone' not in data


def test_import_registrations_error(dummy_regform, dummy_user):
    dummy_user.secondary_emails.add('dummy@example.com')

    create_registration(dummy_regform, {
        'email': dummy_user.email,
        'first_name': dummy_user.first_name,
        'last_name': dummy_user.last_name
    }, notify_user=False)

    create_registration(dummy_regform, {
        'email': 'boss@example.com',
        'first_name': 'Big',
        'last_name': 'Boss'
    }, notify_user=False)

    # duplicate e-mail
    csv = b'\n'.join([b'Big,Boss,ACME Inc.,Supreme Leader,+1-202-555-1337,boss@example.com'])

    with pytest.raises(UserValueError) as e:
        import_registrations_from_csv(dummy_regform, BytesIO(csv))
    assert 'a registration with this email already exists' in str(e.value)
    assert 'Row 1' in str(e.value)

    # duplicate user
    csv = b'\n'.join([b'Big,Boss,ACME Inc.,Supreme Leader,+1-202-555-1337,dummy@example.com'])

    with pytest.raises(UserValueError) as e:
        import_registrations_from_csv(dummy_regform, BytesIO(csv))
    assert 'a registration for this user already exists' in str(e.value)
    assert 'Row 1' in str(e.value)


def test_import_invitations(monkeypatch, dummy_regform, dummy_user):
    monkeypatch.setattr('indico.modules.events.registration.util.notify_invitation', lambda *args, **kwargs: None)

    # normal import with no conflicts
    csv = b'\n'.join([b'Bob,Doe,ACME Inc.,bdoe@example.com',
                      b'Jane,Smith,ACME Inc.,jsmith@example.com'])
    invitations, skipped = import_invitations_from_csv(dummy_regform, BytesIO(csv),
                                                       email_from='noreply@example.com', email_subject='invitation',
                                                       email_body='Invitation to event',
                                                       skip_moderation=False, skip_existing=True)
    assert len(invitations) == 2
    assert skipped == 0

    assert invitations[0].first_name == 'Bob'
    assert invitations[0].last_name == 'Doe'
    assert invitations[0].affiliation == 'ACME Inc.'
    assert invitations[0].email == 'bdoe@example.com'
    assert not invitations[0].skip_moderation

    assert invitations[1].first_name == 'Jane'
    assert invitations[1].last_name == 'Smith'
    assert invitations[1].affiliation == 'ACME Inc.'
    assert invitations[1].email == 'jsmith@example.com'
    assert not invitations[1].skip_moderation


def test_import_invitations_duplicate_invitation(monkeypatch, dummy_regform, dummy_user):
    monkeypatch.setattr('indico.modules.events.registration.util.notify_invitation', lambda *args, **kwargs: None)

    invitation = RegistrationInvitation(skip_moderation=True, email='awang@example.com', first_name='Amy',
                                        last_name='Wang', affiliation='ACME Inc.')
    dummy_regform.invitations.append(invitation)

    # duplicate invitation with 'skip_existing=True'
    csv = b'\n'.join([b'Amy,Wang,ACME Inc.,awang@example.com',
                      b'Jane,Smith,ACME Inc.,jsmith@example.com'])
    invitations, skipped = import_invitations_from_csv(dummy_regform, BytesIO(csv),
                                                       email_from='noreply@example.com', email_subject='invitation',
                                                       email_body='Invitation to event',
                                                       skip_moderation=True, skip_existing=True)
    assert len(invitations) == 1
    assert skipped == 1

    assert invitations[0].first_name == 'Jane'
    assert invitations[0].last_name == 'Smith'
    assert invitations[0].affiliation == 'ACME Inc.'
    assert invitations[0].email == 'jsmith@example.com'
    assert invitations[0].skip_moderation


def test_import_invitations_duplicate_registration(monkeypatch, dummy_regform):
    monkeypatch.setattr('indico.modules.events.registration.util.notify_invitation', lambda *args, **kwargs: None)

    create_registration(dummy_regform, {
        'email': 'boss@example.com',
        'first_name': 'Big',
        'last_name': 'Boss'
    }, notify_user=False)

    # duplicate registration with 'skip_existing=True'
    csv = b'\n'.join([b'Big,Boss,ACME Inc.,boss@example.com',
                      b'Jane,Smith,ACME Inc.,jsmith@example.com'])
    invitations, skipped = import_invitations_from_csv(dummy_regform, BytesIO(csv),
                                                       email_from='noreply@example.com', email_subject='invitation',
                                                       email_body='Invitation to event',
                                                       skip_moderation=True, skip_existing=True)
    assert len(invitations) == 1
    assert skipped == 1

    assert invitations[0].first_name == 'Jane'
    assert invitations[0].last_name == 'Smith'
    assert invitations[0].affiliation == 'ACME Inc.'
    assert invitations[0].email == 'jsmith@example.com'
    assert invitations[0].skip_moderation


def test_import_invitations_duplicate_user(monkeypatch, dummy_regform, dummy_user):
    monkeypatch.setattr('indico.modules.events.registration.util.notify_invitation', lambda *args, **kwargs: None)

    dummy_user.secondary_emails.add('dummy@example.com')
    create_registration(dummy_regform, {
        'email': dummy_user.email,
        'first_name': dummy_user.first_name,
        'last_name': dummy_user.last_name
    }, notify_user=False)

    # duplicate user with 'skip_existing=True'
    csv = b'\n'.join([b'Big,Boss,ACME Inc.,dummy@example.com',
                      b'Jane,Smith,ACME Inc.,jsmith@example.com'])
    invitations, skipped = import_invitations_from_csv(dummy_regform, BytesIO(csv),
                                                       email_from='noreply@example.com', email_subject='invitation',
                                                       email_body='Invitation to event',
                                                       skip_moderation=True, skip_existing=True)
    assert len(invitations) == 1
    assert skipped == 1

    assert invitations[0].first_name == 'Jane'
    assert invitations[0].last_name == 'Smith'
    assert invitations[0].affiliation == 'ACME Inc.'
    assert invitations[0].email == 'jsmith@example.com'
    assert invitations[0].skip_moderation


def test_import_invitations_error(dummy_regform, dummy_user):
    dummy_user.secondary_emails.add('dummy@example.com')

    create_registration(dummy_regform, {
        'email': dummy_user.email,
        'first_name': dummy_user.first_name,
        'last_name': dummy_user.last_name
    }, notify_user=False)

    create_registration(dummy_regform, {
        'email': 'boss@example.com',
        'first_name': 'Big',
        'last_name': 'Boss'
    }, notify_user=False)

    invitation = RegistrationInvitation(skip_moderation=True, email='bdoe@example.com', first_name='Bill',
                                        last_name='Doe', affiliation='ACME Inc.')
    dummy_regform.invitations.append(invitation)

    # duplicate e-mail (registration)
    csv = b'\n'.join([b'Big,Boss,ACME Inc.,boss@example.com'])

    with pytest.raises(UserValueError) as e:
        import_invitations_from_csv(dummy_regform, BytesIO(csv),
                                    email_from='noreply@example.com', email_subject='invitation',
                                    email_body='Invitation to event',
                                    skip_moderation=False, skip_existing=False)
    assert 'a registration with this email already exists' in str(e.value)
    assert 'Row 1' in str(e.value)

    # duplicate user
    csv = b'\n'.join([b'Big,Boss,ACME Inc.,dummy@example.com'])

    with pytest.raises(UserValueError) as e:
        import_invitations_from_csv(dummy_regform, BytesIO(csv),
                                    email_from='noreply@example.com', email_subject='invitation',
                                    email_body='Invitation to event',
                                    skip_moderation=False, skip_existing=False)
    assert 'a registration for this user already exists' in str(e.value)
    assert 'Row 1' in str(e.value)

    # duplicate email (invitation)
    csv = b'\n'.join([b'Bill,Doe,ACME Inc.,bdoe@example.com'])
    with pytest.raises(UserValueError) as e:
        import_invitations_from_csv(dummy_regform, BytesIO(csv),
                                    email_from='noreply@example.com', email_subject='invitation',
                                    email_body='Invitation to event',
                                    skip_moderation=False, skip_existing=False)
    assert 'an invitation for this user already exists' in str(e.value)
    assert 'Row 1' in str(e.value)


@pytest.mark.parametrize(('start_dt', 'end_dt', 'include_scheduled', 'expected_regform_flag'), (
    (datetime(2007, 1, 1, 1, 0, 0), datetime(2007, 2, 1, 1, 0, 0), False, False),
    (datetime(2019, 1, 1, 1, 0, 0), datetime(2020, 2, 1, 1, 0, 0), False, True),
    (datetime(2007, 1, 1, 1, 0, 0), datetime(2007, 2, 1, 1, 0, 0), True, True),
    (datetime(2019, 1, 1, 1, 0, 0), datetime(2020, 2, 1, 1, 0, 0), True, True),
    (None, datetime(2020, 2, 1, 1, 0, 0), False, False),
    (None, datetime(2020, 2, 1, 1, 0, 0), True, False),
    (datetime(2019, 1, 1, 1, 0, 0), None, False, True),
    (None, None, False, False),
    (None, None, True, False)
))
def test_get_event_regforms_no_registration(dummy_event, dummy_user, dummy_regform, freeze_time, start_dt, end_dt,
                                            include_scheduled, expected_regform_flag):
    freeze_time(datetime(2019, 12, 13, 8, 0, 0))
    if start_dt:
        dummy_regform.start_dt = dummy_event.tzinfo.localize(start_dt)
    if end_dt:
        dummy_regform.end_dt = dummy_event.tzinfo.localize(end_dt)

    regforms, registrations = get_event_regforms_registrations(dummy_event, dummy_user, include_scheduled)

    assert (dummy_regform in regforms) == expected_regform_flag
    assert list(registrations.values()) == [None]


@pytest.mark.parametrize(('start_dt', 'end_dt', 'include_scheduled'), (
    (datetime(2019, 1, 1, 1, 0, 0), datetime(2019, 2, 1, 1, 0, 0), True),
    (datetime(2018, 1, 1, 1, 0, 0), datetime(2018, 12, 1, 1, 0, 0), False),
    (datetime(2019, 1, 1, 1, 0, 0), datetime(2020, 2, 1, 1, 0, 0), False),
    (None, None, False),
    (datetime(2008, 1, 1, 1, 0, 0), None, False),
    (None, datetime(2020, 12, 1, 1, 0, 0), True),
))
@pytest.mark.usefixtures('dummy_reg')
def test_get_event_regforms_registration(dummy_event, dummy_user, dummy_regform, start_dt, end_dt, include_scheduled,
                                         freeze_time):
    freeze_time(datetime(2019, 12, 13, 8, 0, 0))
    if start_dt:
        dummy_regform.start_dt = dummy_event.tzinfo.localize(start_dt)
    if end_dt:
        dummy_regform.end_dt = dummy_event.tzinfo.localize(end_dt)

    regforms, registrations = get_event_regforms_registrations(dummy_event, dummy_user, include_scheduled=False)

    assert list(registrations.values())[0].user == dummy_user
    assert dummy_regform in regforms


@pytest.mark.usefixtures('dummy_reg')
def test_get_registered_event_persons(dummy_event, dummy_user, dummy_regform):
    create_registration(dummy_regform, {
        'email': 'john@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
    }, notify_user=False)

    user_person = EventPerson.create_from_user(dummy_user, dummy_event)
    no_user_person = EventPerson(
        email='john@example.com',
        first_name='John',
        last_name='Doe'
    )

    create_registration(dummy_regform, {
        'email': 'jane@example.com',
        'first_name': 'Jane',
        'last_name': 'Doe',
    }, notify_user=False)

    no_user_no_reg = EventPerson(
        email='noshow@example.com',
        first_name='No',
        last_name='Show'
    )
    dummy_event.persons.append(user_person)
    dummy_event.persons.append(no_user_person)
    dummy_event.persons.append(no_user_no_reg)
    db.session.flush()

    registered_persons = get_registered_event_persons(dummy_event)
    assert registered_persons == {user_person, no_user_person}
