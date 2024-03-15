# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.registration.models.form_fields import RegistrationFormField
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.items import RegistrationFormSection
from indico.modules.events.registration.models.registrations import Registration, RegistrationData, RegistrationState
from indico.modules.events.registration.util import create_personal_data_fields


@pytest.fixture
def create_regform(db):
    """Return a callable that lets you create a registration form."""
    def _create_regform(event, title='Registration Form', currency='USD', **kwargs):
        regform = RegistrationForm(event=event, title=title, currency=currency, **kwargs)
        create_personal_data_fields(regform)

        # enable all fields
        for field in regform.sections[0].fields:
            field.is_enabled = True
        db.session.add(regform)
        db.session.flush()
        return regform

    return _create_regform


@pytest.fixture
def dummy_regform(db, dummy_event, create_regform):
    """Create a dummy registration form for the dummy event."""
    return create_regform(dummy_event, id=420)


@pytest.fixture
def dummy_reg(db, dummy_event, dummy_regform, dummy_user):
    """Create a dummy registration for the dummy event."""
    reg = Registration(
        registration_form_id=dummy_regform.id,
        first_name='Guinea',
        last_name='Pig',
        checked_in=True,
        state=RegistrationState.complete,
        currency='USD',
        email='1337@example.test',
        user=dummy_user
    )
    dummy_event.registrations.append(reg)
    db.session.flush()
    return reg


@pytest.fixture
def create_registration(dummy_event):
    """Return a callable that lets you create a registration."""

    def _create_registration(user, regform, **kwargs):
        return Registration(
            first_name='Guinea',
            last_name='Pig',
            checked_in=True,
            state=RegistrationState.complete,
            currency='USD',
            email=user.email,
            user=user,
            registration_form=regform,
            **kwargs
        )

    return _create_registration


def _id(n):
    assert 0 <= n < 10000000
    return f'{n:08d}-0000-0000-0000-000000000000'


@pytest.fixture
def create_accompanying_persons():
    def _create_accompanying_persons(n):
        names = [
            {'firstName': 'Wanda', 'lastName': 'Whizbang'},
            {'firstName': 'Quentin', 'lastName': 'Quibble'},
            {'firstName': 'Gertrude', 'lastName': 'Gigglesnort'},
            {'firstName': 'Buford', 'lastName': 'Bumblebee'},
            {'firstName': 'Penelope', 'lastName': 'Puddlejumper'},
            {'firstName': 'Winston', 'lastName': 'Wobblebottom'},
        ]
        length = len(names)
        return [{'id': _id(i)} | names[i % length] for i in range(n)]
    return _create_accompanying_persons


@pytest.fixture
def create_accompanying_persons_field(db, dummy_regform, create_accompanying_persons):
    def _create_accompanying_persons_field(max_persons, persons_count_against_limit,
                                           registration=None, data=None, num_persons=0):
        section = RegistrationFormSection(
            registration_form=dummy_regform,
            title='dummy_section',
            is_manager_only=False
        )
        db.session.add(section)
        db.session.flush()
        field = RegistrationFormField(
            input_type='accompanying_persons',
            title='Field',
            parent=section,
            registration_form=dummy_regform
        )
        field.field_impl.form_item.data = {
            'max_persons': max_persons,
            'persons_count_against_limit': persons_count_against_limit,
        }
        field.versioned_data = field.field_impl.form_item.data
        if registration:
            registration.data.append(RegistrationData(
                field_data=field.current_data,
                data=(data if data is not None else create_accompanying_persons(num_persons))
            ))
            db.session.flush()
        return field

    return _create_accompanying_persons_field


@pytest.fixture
def dummy_accompanying_persons_field(db, dummy_reg, create_accompanying_persons_field):
    return create_accompanying_persons_field(max_persons=5, persons_count_against_limit=False,
                                             registration=dummy_reg, num_persons=5)
