# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
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
from indico.modules.events.registration.util import (create_registration, get_event_regforms_registrations,
                                                     get_registered_event_persons, import_registrations_from_csv)


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


def _dummy_csv(csv_content, csv_header):
    csv = b'\n'.join(csv_header + csv_content)
    return BytesIO(csv.encode('utf-8'))


@pytest.mark.parametrize(
    'csv_header', [[
        'first_name:Personal Data#First Name,'
        'last_name:Personal Data#Last Name,'
        'affiliation:Personal Data#Affiliation,'
        'position:Personal Data#Position,'
        'phone:Personal Data#Phone Number,'
        'email:Personal Data#Email Address,'
    ], [
        'Personal Data#First Name,'
        'Personal Data#Last Name,'
        'Personal Data#Affiliation,'
        'Personal Data#Position,'
        'Personal Data#Phone Number,'
        'Personal Data#Email Address,'
    ], ['first_name,'
        'last_name,'
        'affiliation,'
        'position,'
        'phone,'
        'email,']],
    ids=["long form", "section/field", "html field name"])
def test_import_registrations(dummy_regform, dummy_user, csv_header):

    # current available fields
    # [u'title:Personal Data#Title,first_name:Personal Data#First Name,
    #  last_name:Personal Data#Last Name,email:Personal Data#Email Address,
    #  affiliation:Personal Data#Affiliation,address:Personal Data#Address,
    #  country:Personal Data#Country,phone:Personal Data#Phone Number,
    #  position:Personal Data#Position']

    csv_content = [
        'John,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,jdoe@example.com',
        'Jane,Smith,ACME Inc.,CEO,,jane@example.com', u'Billy Bob,Doe,,,,1337@example.COM'
    ]

    registrations, skipped = import_registrations_from_csv(dummy_regform, _dummy_csv(csv_content, csv_header))
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
    # the trailing comma in the headers creates an extra column
    assert skipped == 1


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


_csv_header_def = [
    'first_name:Personal Data#First Name,'
    'last_name:Personal Data#Last Name,'
    'affiliation:Personal Data#Affiliation,'
    'position:Personal Data#Position,'
    'phone:Personal Data#Phone Number,'
    'email:Personal Data#Email Address,'
]
_csv_header_no_mail = [
    'first_name:Personal Data#First Name,'
    'last_name:Personal Data#Last Name,'
    'affiliation:Personal Data#Affiliation,'
    'position:Personal Data#Position,'
    'phone:Personal Data#Phone Number,'
]


@pytest.mark.parametrize(
    'csv_content,csv_header,expected,row', [
        ([b'John,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,jdoe@example.com', b'Buggy,Entry,ACME Inc.,CEO,'],
         _csv_header_no_mail, 'Missing required fields', 0),
        ([b'John,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,jdoe@example.com', b'Buggy,Entry,ACME Inc.,CEO,'],
         _csv_header_def, 'missing e-mail', 2),
        ([
            b'Bill,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,bdoe@example.com',
            b'Buggy,Entry,ACME Inc.,CEO,,not-an-email'
        ], _csv_header_def, 'invalid e-mail', 2),
        ([
            b'Bill,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,bdoe@example.com',
            b'Bob,Doe,ACME Inc.,Boss,,bdoe@example.com'
        ], _csv_header_def, 'email address is not unique', 2),
        ([b'Big,Boss,ACME Inc.,Supreme Leader,+1-202-555-1337,boss@example.com'], _csv_header_def,
         'a registration with this email already exists', 1),
        ([
            b'Ray,Doe,ACME Inc.,Regional Manager,+1-202-555-0140,rdoe@example.com',
            b',Buggy,ACME Inc.,CEO,,buggy@example.com'
        ], _csv_header_def, 'missing first', 2),
    ],
    ids=[
        'missing column', 'missing email', 'invalid email', 'duplicate email(csv)', 'duplicate email(registration)',
        'missing first name'
    ])
def test_import_error(dummy_regform, csv_content, csv_header, expected, row):
    create_registration(
        dummy_regform, {'email': 'boss@example.com',
                        'first_name': 'Big',
                        'last_name': 'Boss'}, notify_user=False)

    with pytest.raises(UserValueError) as e:
        import_registrations_from_csv(dummy_regform, _dummy_csv(csv_content, csv_header))
    assert expected in e.value.args[0]
    if row != 0:
        assert 'Row {}'.format(row) in e.value.args[0]
    else:
        assert 'Header:' in e.value.args[0]
