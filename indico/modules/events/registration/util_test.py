# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime
from io import BytesIO

import pytest
from flask import session

from indico.core.db import db
from indico.core.errors import UserValueError
from indico.modules.events.models.persons import EventPerson
from indico.modules.events.registration.controllers.management.fields import _fill_form_field_with_data
from indico.modules.events.registration.models.form_fields import RegistrationFormField
from indico.modules.events.registration.models.invitations import RegistrationInvitation
from indico.modules.events.registration.models.items import RegistrationFormItemType, RegistrationFormSection
from indico.modules.events.registration.util import (create_registration, get_event_regforms_registrations,
                                                     get_registered_event_persons, get_user_data,
                                                     import_invitations_from_csv, import_registrations_from_csv,
                                                     import_user_records_from_csv, modify_registration)
from indico.modules.users.models.users import UserTitle


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


def test_import_users(dummy_regform):
    csv = b'\n'.join([b'John,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,jdoe@example.test',
                      b'Jane,Smith,ACME Inc.,CEO,,jane@example.test',
                      b'Billy Bob,Doe,,,,1337@EXAMPLE.test'])

    columns = ['first_name', 'last_name', 'affiliation', 'position', 'phone', 'email']
    users = import_user_records_from_csv(BytesIO(csv), columns)
    assert len(users) == 3

    assert users[0] == {
        'first_name': 'John',
        'last_name': 'Doe',
        'affiliation': 'ACME Inc.',
        'position': 'Regional Manager',
        'phone': '+1-202-555-0140',
        'email': 'jdoe@example.test',
    }

    assert users[1] == {
        'first_name': 'Jane',
        'last_name': 'Smith',
        'affiliation': 'ACME Inc.',
        'position': 'CEO',
        'phone': '',
        'email': 'jane@example.test',
    }

    assert users[2] == {
        'first_name': 'Billy Bob',
        'last_name': 'Doe',
        'affiliation': '',
        'position': '',
        'phone': '',
        'email': '1337@example.test',
    }


def test_import_users_error(create_user):
    columns = ['first_name', 'last_name', 'affiliation', 'position', 'phone', 'email']
    user = create_user(123, email='test1@example.test')
    user.secondary_emails.add('test2@example.test')

    # missing column
    csv = b'\n'.join([b'John,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,jdoe@example.test',
                      b'Buggy,Entry,ACME Inc.,CEO,'])

    with pytest.raises(UserValueError) as e:
        import_user_records_from_csv(BytesIO(csv), columns)
    assert 'malformed' in str(e.value)
    assert 'Row 2' in str(e.value)

    # missing e-mail
    csv = b'\n'.join([b'Bill,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,bdoe@example.test',
                      b'Buggy,Entry,ACME Inc.,CEO,,'])

    with pytest.raises(UserValueError) as e:
        import_user_records_from_csv(BytesIO(csv), columns)
    assert 'missing e-mail' in str(e.value)
    assert 'Row 2' in str(e.value)

    # bad e-mail
    csv = b'\n'.join([b'Bill,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,bdoe@example.test',
                      b'Buggy,Entry,ACME Inc.,CEO,,not-an-email'])

    with pytest.raises(UserValueError) as e:
        import_user_records_from_csv(BytesIO(csv), columns)
    assert 'invalid e-mail' in str(e.value)
    assert 'Row 2' in str(e.value)

    # duplicate e-mail
    csv = b'\n'.join([b'Bill,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,bdoe@example.test',
                      b'Bob,Doe,ACME Inc.,Boss,,bdoe@example.test'])

    with pytest.raises(UserValueError) as e:
        import_user_records_from_csv(BytesIO(csv), columns)
    assert 'email address is not unique' in str(e.value)
    assert 'Row 2' in str(e.value)

    # duplicate user
    csv = b'\n'.join([b'Big,Boss,ACME Inc.,Supreme Leader,+1-202-555-1337,test1@example.test',
                      b'Little,Boss,ACME Inc.,Wannabe Leader,+1-202-555-1338,test2@EXAMPLE.test'])

    with pytest.raises(UserValueError) as e:
        import_user_records_from_csv(BytesIO(csv), columns)
    assert 'Row 2: email address belongs to the same user as in row 1' in str(e.value)

    # missing first name
    csv = b'\n'.join([b'Ray,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,rdoe@example.test',
                      b',Buggy,ACME Inc.,CEO,,buggy@example.test'])

    with pytest.raises(UserValueError) as e:
        import_user_records_from_csv(BytesIO(csv), columns)
    assert 'missing first' in str(e.value)
    assert 'Row 2' in str(e.value)


def test_import_registrations(dummy_regform, dummy_user):
    csv = b'\n'.join([b'John,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,jdoe@example.test',
                      b'Jane,Smith,ACME Inc.,CEO,,jane@example.test',
                      b'Billy Bob,Doe,,,,1337@EXAMPLE.test'])
    registrations = import_registrations_from_csv(dummy_regform, BytesIO(csv))
    assert len(registrations) == 3

    assert registrations[0].full_name == 'John Doe'
    assert registrations[0].user is None
    data = registrations[0].get_personal_data()
    assert data['affiliation'] == 'ACME Inc.'
    assert data['email'] == 'jdoe@example.test'
    assert data['position'] == 'Regional Manager'
    assert data['phone'] == '+1-202-555-0140'

    assert registrations[1].full_name == 'Jane Smith'
    assert registrations[1].user is None
    data = registrations[1].get_personal_data()
    assert data['affiliation'] == 'ACME Inc.'
    assert data['email'] == 'jane@example.test'
    assert data['position'] == 'CEO'
    assert 'phone' not in data

    assert registrations[2].full_name == 'Billy Bob Doe'
    assert registrations[2].user == dummy_user
    data = registrations[2].get_personal_data()
    assert 'affiliation' not in data
    assert data['email'] == '1337@example.test'
    assert 'position' not in data
    assert 'phone' not in data


def test_import_registrations_error(dummy_regform, dummy_user):
    dummy_user.secondary_emails.add('dummy@example.test')

    create_registration(dummy_regform, {
        'email': dummy_user.email,
        'first_name': dummy_user.first_name,
        'last_name': dummy_user.last_name
    }, notify_user=False)

    create_registration(dummy_regform, {
        'email': 'boss@example.test',
        'first_name': 'Big',
        'last_name': 'Boss'
    }, notify_user=False)

    # duplicate e-mail
    csv = b'\n'.join([b'Big,Boss,ACME Inc.,Supreme Leader,+1-202-555-1337,boss@example.test'])

    with pytest.raises(UserValueError) as e:
        import_registrations_from_csv(dummy_regform, BytesIO(csv))
    assert 'a registration with this email already exists' in str(e.value)
    assert 'Row 1' in str(e.value)

    # duplicate user
    csv = b'\n'.join([b'Big,Boss,ACME Inc.,Supreme Leader,+1-202-555-1337,dummy@example.test'])

    with pytest.raises(UserValueError) as e:
        import_registrations_from_csv(dummy_regform, BytesIO(csv))
    assert 'a registration for this user already exists' in str(e.value)
    assert 'Row 1' in str(e.value)


def test_import_invitations(monkeypatch, dummy_regform, dummy_user):
    monkeypatch.setattr('indico.modules.events.registration.util.notify_invitation', lambda *args, **kwargs: None)

    # normal import with no conflicts
    csv = b'\n'.join([b'Bob,Doe,ACME Inc.,bdoe@example.test',
                      b'Jane,Smith,ACME Inc.,jsmith@example.test'])
    invitations, skipped = import_invitations_from_csv(dummy_regform, BytesIO(csv),
                                                       email_from='noreply@example.test', email_subject='invitation',
                                                       email_body='Invitation to event',
                                                       skip_moderation=False, skip_existing=True)
    assert len(invitations) == 2
    assert skipped == 0

    assert invitations[0].first_name == 'Bob'
    assert invitations[0].last_name == 'Doe'
    assert invitations[0].affiliation == 'ACME Inc.'
    assert invitations[0].email == 'bdoe@example.test'
    assert not invitations[0].skip_moderation

    assert invitations[1].first_name == 'Jane'
    assert invitations[1].last_name == 'Smith'
    assert invitations[1].affiliation == 'ACME Inc.'
    assert invitations[1].email == 'jsmith@example.test'
    assert not invitations[1].skip_moderation


def test_import_invitations_duplicate_invitation(monkeypatch, dummy_regform, dummy_user):
    monkeypatch.setattr('indico.modules.events.registration.util.notify_invitation', lambda *args, **kwargs: None)

    invitation = RegistrationInvitation(skip_moderation=True, email='awang@example.test', first_name='Amy',
                                        last_name='Wang', affiliation='ACME Inc.')
    dummy_regform.invitations.append(invitation)

    # duplicate invitation with 'skip_existing=True'
    csv = b'\n'.join([b'Amy,Wang,ACME Inc.,awang@example.test',
                      b'Jane,Smith,ACME Inc.,jsmith@example.test'])
    invitations, skipped = import_invitations_from_csv(dummy_regform, BytesIO(csv),
                                                       email_from='noreply@example.test', email_subject='invitation',
                                                       email_body='Invitation to event',
                                                       skip_moderation=True, skip_existing=True)
    assert len(invitations) == 1
    assert skipped == 1

    assert invitations[0].first_name == 'Jane'
    assert invitations[0].last_name == 'Smith'
    assert invitations[0].affiliation == 'ACME Inc.'
    assert invitations[0].email == 'jsmith@example.test'
    assert invitations[0].skip_moderation


def test_import_invitations_duplicate_registration(monkeypatch, dummy_regform):
    monkeypatch.setattr('indico.modules.events.registration.util.notify_invitation', lambda *args, **kwargs: None)

    create_registration(dummy_regform, {
        'email': 'boss@example.test',
        'first_name': 'Big',
        'last_name': 'Boss'
    }, notify_user=False)

    # duplicate registration with 'skip_existing=True'
    csv = b'\n'.join([b'Big,Boss,ACME Inc.,boss@example.test',
                      b'Jane,Smith,ACME Inc.,jsmith@example.test'])
    invitations, skipped = import_invitations_from_csv(dummy_regform, BytesIO(csv),
                                                       email_from='noreply@example.test', email_subject='invitation',
                                                       email_body='Invitation to event',
                                                       skip_moderation=True, skip_existing=True)
    assert len(invitations) == 1
    assert skipped == 1

    assert invitations[0].first_name == 'Jane'
    assert invitations[0].last_name == 'Smith'
    assert invitations[0].affiliation == 'ACME Inc.'
    assert invitations[0].email == 'jsmith@example.test'
    assert invitations[0].skip_moderation


def test_import_invitations_duplicate_user(monkeypatch, dummy_regform, dummy_user):
    monkeypatch.setattr('indico.modules.events.registration.util.notify_invitation', lambda *args, **kwargs: None)

    dummy_user.secondary_emails.add('dummy@example.test')
    create_registration(dummy_regform, {
        'email': dummy_user.email,
        'first_name': dummy_user.first_name,
        'last_name': dummy_user.last_name
    }, notify_user=False)

    # duplicate user with 'skip_existing=True'
    csv = b'\n'.join([b'Big,Boss,ACME Inc.,dummy@example.test',
                      b'Jane,Smith,ACME Inc.,jsmith@example.test'])
    invitations, skipped = import_invitations_from_csv(dummy_regform, BytesIO(csv),
                                                       email_from='noreply@example.test', email_subject='invitation',
                                                       email_body='Invitation to event',
                                                       skip_moderation=True, skip_existing=True)
    assert len(invitations) == 1
    assert skipped == 1

    assert invitations[0].first_name == 'Jane'
    assert invitations[0].last_name == 'Smith'
    assert invitations[0].affiliation == 'ACME Inc.'
    assert invitations[0].email == 'jsmith@example.test'
    assert invitations[0].skip_moderation


def test_import_invitations_error(dummy_regform, dummy_user):
    dummy_user.secondary_emails.add('dummy@example.test')

    create_registration(dummy_regform, {
        'email': dummy_user.email,
        'first_name': dummy_user.first_name,
        'last_name': dummy_user.last_name
    }, notify_user=False)

    create_registration(dummy_regform, {
        'email': 'boss@example.test',
        'first_name': 'Big',
        'last_name': 'Boss'
    }, notify_user=False)

    invitation = RegistrationInvitation(skip_moderation=True, email='bdoe@example.test', first_name='Bill',
                                        last_name='Doe', affiliation='ACME Inc.')
    dummy_regform.invitations.append(invitation)

    # duplicate e-mail (registration)
    csv = b'\n'.join([b'Big,Boss,ACME Inc.,boss@example.test'])

    with pytest.raises(UserValueError) as e:
        import_invitations_from_csv(dummy_regform, BytesIO(csv),
                                    email_from='noreply@example.test', email_subject='invitation',
                                    email_body='Invitation to event',
                                    skip_moderation=False, skip_existing=False)
    assert 'a registration with this email already exists' in str(e.value)
    assert 'Row 1' in str(e.value)

    # duplicate user
    csv = b'\n'.join([b'Big,Boss,ACME Inc.,dummy@example.test'])

    with pytest.raises(UserValueError) as e:
        import_invitations_from_csv(dummy_regform, BytesIO(csv),
                                    email_from='noreply@example.test', email_subject='invitation',
                                    email_body='Invitation to event',
                                    skip_moderation=False, skip_existing=False)
    assert 'a registration for this user already exists' in str(e.value)
    assert 'Row 1' in str(e.value)

    # duplicate email (invitation)
    csv = b'\n'.join([b'Bill,Doe,ACME Inc.,bdoe@example.test'])
    with pytest.raises(UserValueError) as e:
        import_invitations_from_csv(dummy_regform, BytesIO(csv),
                                    email_from='noreply@example.test', email_subject='invitation',
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
        'email': 'john@example.test',
        'first_name': 'John',
        'last_name': 'Doe',
    }, notify_user=False)

    user_person = EventPerson.create_from_user(dummy_user, dummy_event)
    no_user_person = EventPerson(
        email='john@example.test',
        first_name='John',
        last_name='Doe'
    )

    create_registration(dummy_regform, {
        'email': 'jane@example.test',
        'first_name': 'Jane',
        'last_name': 'Doe',
    }, notify_user=False)

    no_user_no_reg = EventPerson(
        email='noshow@example.test',
        first_name='No',
        last_name='Show'
    )
    dummy_event.persons.append(user_person)
    dummy_event.persons.append(no_user_person)
    dummy_event.persons.append(no_user_no_reg)
    db.session.flush()

    registered_persons = get_registered_event_persons(dummy_event)
    assert registered_persons == {user_person, no_user_person}


def test_create_registration(monkeypatch, dummy_event, dummy_user, dummy_regform):
    monkeypatch.setattr('indico.modules.users.util.get_user_by_email', lambda *args, **kwargs: dummy_user)

    # Extend the dummy_regform with more sections and fields
    section = RegistrationFormSection(registration_form=dummy_regform, title='dummy_section', is_manager_only=False)
    db.session.add(section)
    db.session.flush()

    boolean_field = RegistrationFormField(parent_id=section.id, registration_form=dummy_regform)
    _fill_form_field_with_data(boolean_field, {
        'input_type': 'bool', 'default_value': False, 'title': 'Yes/No'
    })
    db.session.add(boolean_field)

    multi_choice_field = RegistrationFormField(parent_id=section.id, registration_form=dummy_regform)
    _fill_form_field_with_data(multi_choice_field, {
        'input_type': 'multi_choice', 'with_extra_slots': False, 'title': 'Multi Choice',
        'choices': [
            {'caption': 'A', 'id': 'new:test1', 'is_enabled': True},
            {'caption': 'B', 'id': 'new:test2', 'is_enabled': True},
        ]
    })
    db.session.add(multi_choice_field)
    db.session.flush()

    data = {
        boolean_field.html_field_name: True,
        multi_choice_field.html_field_name: {'test1': 2},
        'email': dummy_user.email, 'first_name': dummy_user.first_name, 'last_name': dummy_user.last_name}
    reg = create_registration(dummy_regform, data, invitation=None, management=False, notify_user=False)

    assert reg.data_by_field[boolean_field.id].data
    assert reg.data_by_field[multi_choice_field.id].data == {'test1': 2}
    db.session.delete(reg)
    db.session.flush()

    # Make sure that missing data gets default values:
    data = {
        'email': dummy_user.email, 'first_name': dummy_user.first_name, 'last_name': dummy_user.last_name}
    reg = create_registration(dummy_regform, data, invitation=None, management=False, notify_user=False)

    assert not reg.data_by_field[boolean_field.id].data
    assert reg.data_by_field[multi_choice_field.id].data == {}
    db.session.delete(reg)
    db.session.flush()

    # Add a manager only section
    section = RegistrationFormSection(registration_form=dummy_regform, title='manager_section', is_manager_only=True)
    db.session.add(section)
    db.session.flush()

    checkbox_field = RegistrationFormField(parent_id=section.id, registration_form=dummy_regform)
    _fill_form_field_with_data(checkbox_field, {
        'input_type': 'checkbox', 'title': 'Checkbox'
    })
    db.session.add(checkbox_field)
    db.session.flush()

    data = {
        checkbox_field.html_field_name: True,
        'email': dummy_user.email, 'first_name': dummy_user.first_name, 'last_name': dummy_user.last_name}
    reg = create_registration(dummy_regform, data, invitation=None, management=False, notify_user=False)

    assert not reg.data_by_field[boolean_field.id].data
    assert reg.data_by_field[multi_choice_field.id].data == {}
    # Assert that the manager field gets the default value, not the value sent
    assert not reg.data_by_field[checkbox_field.id].data
    db.session.delete(reg)
    db.session.flush()

    # Try again with management=True
    data = {
        checkbox_field.html_field_name: True,
        'email': dummy_user.email, 'first_name': dummy_user.first_name, 'last_name': dummy_user.last_name}
    reg = create_registration(dummy_regform, data, invitation=None, management=True, notify_user=False)

    assert not reg.data_by_field[boolean_field.id].data
    assert reg.data_by_field[multi_choice_field.id].data == {}
    # Assert that the manager field gets properly set with management=True
    assert reg.data_by_field[checkbox_field.id].data


@pytest.mark.usefixtures('request_context')
def test_modify_registration(monkeypatch, dummy_event, dummy_user, dummy_regform):
    session.set_session_user(dummy_user)
    monkeypatch.setattr('indico.modules.users.util.get_user_by_email', lambda *args, **kwargs: dummy_user)

    # Extend the dummy_regform with more sections and fields
    user_section = RegistrationFormSection(registration_form=dummy_regform,
                                           title='dummy_section', is_manager_only=False)
    db.session.add(user_section)
    db.session.flush()

    boolean_field = RegistrationFormField(parent_id=user_section.id, registration_form=dummy_regform)
    _fill_form_field_with_data(boolean_field, {
        'input_type': 'bool', 'default_value': False, 'title': 'Yes/No'
    })
    db.session.add(boolean_field)

    multi_choice_field = RegistrationFormField(parent_id=user_section.id, registration_form=dummy_regform)
    _fill_form_field_with_data(multi_choice_field, {
        'input_type': 'multi_choice', 'with_extra_slots': False, 'title': 'Multi Choice',
        'choices': [
            {'caption': 'A', 'id': 'new:test1', 'is_enabled': True},
            {'caption': 'B', 'id': 'new:test2', 'is_enabled': True},
        ]
    })
    choice_uuid = next(k for k, v in multi_choice_field.data['captions'].items() if v == 'A')
    db.session.add(multi_choice_field)
    db.session.flush()

    # Add a manager-only section
    management_section = RegistrationFormSection(registration_form=dummy_regform,
                                                 title='manager_section', is_manager_only=True)
    db.session.add(management_section)
    db.session.flush()

    checkbox_field = RegistrationFormField(parent_id=management_section.id, registration_form=dummy_regform)
    _fill_form_field_with_data(checkbox_field, {
        'input_type': 'checkbox', 'is_required': True, 'title': 'Checkbox'
    })
    db.session.add(checkbox_field)
    db.session.flush()

    # Create a registration
    data = {
        boolean_field.html_field_name: True,
        multi_choice_field.html_field_name: {choice_uuid: 2},
        checkbox_field.html_field_name: True,
        'email': dummy_user.email, 'first_name': dummy_user.first_name, 'last_name': dummy_user.last_name}
    reg = create_registration(dummy_regform, data, invitation=None, management=True, notify_user=False)

    assert reg.data_by_field[boolean_field.id].data
    assert reg.data_by_field[multi_choice_field.id].data == {choice_uuid: 2}
    assert reg.data_by_field[checkbox_field.id].data

    # Modify the registration
    data = {
        boolean_field.html_field_name: True,
        multi_choice_field.html_field_name: {choice_uuid: 1},
        checkbox_field.html_field_name: False,
    }
    modify_registration(reg, data, management=False, notify_user=False)

    assert reg.data_by_field[boolean_field.id].data
    assert reg.data_by_field[multi_choice_field.id].data == {choice_uuid: 1}
    # Assert that the manager field is not changed
    assert reg.data_by_field[checkbox_field.id].data

    # Modify as a manager
    data = {
        multi_choice_field.html_field_name: {choice_uuid: 3},
        checkbox_field.html_field_name: False,
    }
    modify_registration(reg, data, management=True, notify_user=False)

    assert reg.data_by_field[boolean_field.id].data
    assert reg.data_by_field[multi_choice_field.id].data == {choice_uuid: 3}
    assert not reg.data_by_field[checkbox_field.id].data

    # Add a new field after registering
    new_multi_choice_field = RegistrationFormField(parent_id=user_section.id, registration_form=dummy_regform)
    _fill_form_field_with_data(new_multi_choice_field, {
        'input_type': 'multi_choice', 'with_extra_slots': False, 'title': 'Multi Choice',
        'choices': [
            {'caption': 'A', 'id': 'new:test3', 'is_enabled': True},
        ]
    })
    db.session.add(new_multi_choice_field)
    db.session.flush()

    modify_registration(reg, {}, management=False, notify_user=False)

    assert reg.data_by_field[boolean_field.id].data
    assert reg.data_by_field[multi_choice_field.id].data == {choice_uuid: 3}
    assert not reg.data_by_field[checkbox_field.id].data
    # Assert that the new field got a default value
    assert reg.data_by_field[new_multi_choice_field.id].data == {}

    # Remove a field after registering
    multi_choice_field.is_deleted = True
    db.session.flush()

    data = {
        multi_choice_field.html_field_name: {choice_uuid: 7},
    }
    modify_registration(reg, data, management=True, notify_user=False)
    assert reg.data_by_field[boolean_field.id].data
    # Assert that the removed field keeps its old value
    assert reg.data_by_field[multi_choice_field.id].data == {choice_uuid: 3}
    assert not reg.data_by_field[checkbox_field.id].data
    assert reg.data_by_field[new_multi_choice_field.id].data == {}


@pytest.mark.usefixtures('request_context')
def test_get_user_data(monkeypatch, dummy_event, dummy_user, dummy_regform):
    monkeypatch.setattr('indico.modules.events.registration.util.notify_invitation', lambda *args, **kwargs: None)
    session.set_session_user(dummy_user)

    assert get_user_data(dummy_regform, None) == {}

    expected = {'email': '1337@example.test', 'first_name': 'Guinea',
                'last_name': 'Pig'}

    user_data = get_user_data(dummy_regform, dummy_user)
    assert user_data == expected

    user_data = get_user_data(dummy_regform, session.user)
    assert user_data == expected

    dummy_user.title = UserTitle.mr
    dummy_user.phone = '+1 22 50 14'
    dummy_user.address = 'Geneva'
    user_data = get_user_data(dummy_regform, dummy_user)
    assert type(user_data['title']) is dict
    assert user_data['phone'] == '+1 22 50 14'

    # Check that data is taken from the invitation
    invitation = RegistrationInvitation(skip_moderation=True, email='awang@example.test', first_name='Amy',
                                        last_name='Wang', affiliation='ACME Inc.')
    dummy_regform.invitations.append(invitation)

    dummy_user.title = None
    user_data = get_user_data(dummy_regform, dummy_user, invitation)
    assert user_data == {'email': 'awang@example.test', 'first_name': 'Amy', 'last_name': 'Wang',
                         'phone': '+1 22 50 14', 'address': 'Geneva', 'affiliation': 'ACME Inc.'}

    # Check that data is taken from the invitation when user is missing
    user_data = get_user_data(dummy_regform, None, invitation)
    assert user_data == {'email': 'awang@example.test', 'first_name': 'Amy', 'last_name': 'Wang',
                         'affiliation': 'ACME Inc.'}

    # Check that data from disabled/deleted fields is not used
    title_field = next(item for item in dummy_regform.active_fields
                       if item.type == RegistrationFormItemType.field_pd and item.personal_data_type.name == 'title')
    title_field.is_enabled = False

    dummy_user.title = UserTitle.dr
    user_data = get_user_data(dummy_regform, dummy_user)
    assert 'title' not in user_data

    phone_field = next(item for item in dummy_regform.active_fields
                       if item.type == RegistrationFormItemType.field_pd and item.personal_data_type.name == 'phone')
    phone_field.is_deleted = True

    user_data = get_user_data(dummy_regform, dummy_user)
    assert 'title' not in user_data
    assert 'phone' not in user_data
    assert user_data == {'email': '1337@example.test', 'first_name': 'Guinea',
                         'last_name': 'Pig', 'address': 'Geneva'}

    for item in dummy_regform.active_fields:
        item.is_enabled = False

    assert get_user_data(dummy_regform, dummy_user) == {}
    assert get_user_data(dummy_regform, dummy_user, invitation) == {}
