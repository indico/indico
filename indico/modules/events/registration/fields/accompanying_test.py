# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from marshmallow import ValidationError

from indico.modules.events.features.util import set_feature_enabled
from indico.modules.events.registration.models.form_fields import RegistrationFormField
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.items import RegistrationFormSection
from indico.modules.events.registration.models.registrations import Registration, RegistrationData, RegistrationState


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


def _id(n):
    assert 0 <= n < 10000000
    return f'{n:08d}-0000-0000-0000-000000000000'


@pytest.fixture
def create_accompanying_persons_field(db, dummy_regform):
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
                data=(data if data is not None else _create_accompanying_persons(num_persons))
            ))
            db.session.flush()
        return field

    return _create_accompanying_persons_field


@pytest.fixture
def create_registration(db, dummy_event, dummy_regform, create_user):
    def _create_registration(user_id):
        user = create_user(user_id)
        reg = Registration(
            first_name='Guinea',
            last_name='Pig',
            checked_in=True,
            state=RegistrationState.complete,
            currency='USD',
            email=user.email,
            user=user,
            registration_form=dummy_regform
        )
        dummy_event.registrations.append(reg)
        db.session.flush()
        return reg

    return _create_registration


def _create_accompanying_persons(n):
    return [{'id': _id(i), 'firstName': 'Guinea', 'lastName': 'Pig'} for i in range(n)]


def _assert_occupied_slots(registration, count):
    assert registration.occupied_slots == count
    assert (Registration.query.with_parent(registration.registration_form)
            .filter(Registration.occupied_slots == count)
            .count() == 1)


def _assert_registration_count(regform, count):
    assert regform.active_registration_count == count
    assert (RegistrationForm.query.with_parent(regform.event)
            .filter(RegistrationForm.active_registration_count == count)
            .count() == 1)
    assert regform.existing_registrations_count == count
    assert (RegistrationForm.query.with_parent(regform.event)
            .filter(RegistrationForm.existing_registrations_count == count)
            .count() == 1)


@pytest.mark.parametrize(('max_persons', 'persons_count_against_limit', 'registration_limit', 'expected_limit'), (
    (0, False, None, None),
    (5, False, None, 5),
    (0, True, None, None),
    (10, True, None, 10),
    (10, True, 5, 4),
    (10, True, 15, 10),
    (0, False, 1, None),
    (5, False, 1, 5),
))
def test_new_registration(dummy_event, dummy_regform, create_accompanying_persons_field, max_persons,
                          persons_count_against_limit, registration_limit, expected_limit):
    set_feature_enabled(dummy_event, 'registration', True)

    field = create_accompanying_persons_field(max_persons, persons_count_against_limit)
    validator = field.field_impl.get_validators(None)
    dummy_regform.registration_limit = registration_limit

    assert field.field_impl._get_field_available_places(None) == expected_limit
    assert not dummy_regform.limit_reached
    validator(_create_accompanying_persons(0))
    if expected_limit:
        validator(_create_accompanying_persons(expected_limit))
        with pytest.raises(ValidationError):
            validator(_create_accompanying_persons(expected_limit + 1))
    else:
        validator(_create_accompanying_persons(1))
        validator(_create_accompanying_persons(10))


@pytest.mark.parametrize(('max_persons', 'persons_count_against_limit', 'registration_limit'), (
    (0, False, None),
    (5, False, None),
    (0, True, None),
    (10, True, None),
    (10, True, 5),
    (10, True, 15),
    (0, False, 1),
    (5, False, 1),
))
@pytest.mark.parametrize('num_persons', (0, 1, 5, 10, 15, 20))
@pytest.mark.usefixtures('dummy_reg')
def test_modifying_registration_field_untouched(db, dummy_event, dummy_regform, create_accompanying_persons_field,
                                                max_persons, persons_count_against_limit, registration_limit,
                                                num_persons):
    set_feature_enabled(dummy_event, 'registration', True)

    dummy_regform.registration_limit = registration_limit
    expected_occupied_slots = 1 + num_persons if persons_count_against_limit else 1
    reg = dummy_event.registrations.one()
    data = _create_accompanying_persons(num_persons)
    field = create_accompanying_persons_field(max_persons, persons_count_against_limit, registration=reg, data=data)
    db.session.flush()
    validator = field.field_impl.get_validators(reg)

    _assert_occupied_slots(reg, expected_occupied_slots)
    _assert_registration_count(dummy_regform, expected_occupied_slots)
    if registration_limit and expected_occupied_slots >= registration_limit:
        assert dummy_regform.limit_reached
    else:
        assert not dummy_regform.limit_reached
    validator(data)


@pytest.mark.parametrize(('max_persons', 'persons_count_against_limit', 'registration_limit', 'expected_limit'), (
    (0, False, None, None),
    (5, False, None, 5),
    (0, True, None, None),
    (10, True, None, 10),
    (10, True, 5, 4),
    (10, True, 15, 10),
    (0, False, 1, None),
    (5, False, 1, 5),
))
@pytest.mark.parametrize(('old_num_persons', 'new_num_persons'), (
    # Same or lower count
    (0, 0), (1, 1), (1, 0),
    (5, 5), (5, 3),
    (10, 10), (10, 9),
    (15, 15), (15, 14), (15, 9),
    (20, 20), (20, 19), (20, 14), (20, 9),
    # Higher count
    (0, 4), (0, 5), (0, 6),
    (1, 4), (1, 5), (1, 11),
    (5, 6), (5, 10), (5, 11),
    (10, 11), (10, 15), (20, 21),
))
@pytest.mark.usefixtures('dummy_reg')
def test_modifying_registration_field_changed(dummy_event, dummy_regform, create_accompanying_persons_field,
                                              max_persons, persons_count_against_limit, registration_limit,
                                              expected_limit, old_num_persons, new_num_persons):
    set_feature_enabled(dummy_event, 'registration', True)

    dummy_regform.registration_limit = registration_limit
    expected_occupied_slots = 1 + old_num_persons if persons_count_against_limit else 1
    reg = dummy_event.registrations.one()
    field = create_accompanying_persons_field(max_persons, persons_count_against_limit,
                                              registration=reg, num_persons=old_num_persons)
    validator = field.field_impl.get_validators(reg)

    _assert_occupied_slots(reg, expected_occupied_slots)
    _assert_registration_count(dummy_regform, expected_occupied_slots)
    assert field.field_impl._get_field_available_places(reg) == expected_limit
    if registration_limit and expected_occupied_slots >= registration_limit:
        assert dummy_regform.limit_reached
    else:
        assert not dummy_regform.limit_reached
    if expected_limit and new_num_persons > old_num_persons and new_num_persons > expected_limit:
        with pytest.raises(ValidationError):
            validator(_create_accompanying_persons(new_num_persons))
    else:
        validator(_create_accompanying_persons(new_num_persons))


def test_registration_count_multiple_fields(dummy_regform, create_accompanying_persons_field, create_registration):
    assert not dummy_regform.limit_reached
    dummy_regform.registration_limit = 5
    assert not dummy_regform.limit_reached
    dummy_regform.registration_limit = None

    _assert_registration_count(dummy_regform, 0)
    reg_1 = create_registration(1)
    _assert_occupied_slots(reg_1, 1)
    _assert_registration_count(dummy_regform, 1)

    create_accompanying_persons_field(0, False, registration=reg_1, num_persons=1)
    _assert_occupied_slots(reg_1, 1)
    _assert_registration_count(dummy_regform, 1)

    create_accompanying_persons_field(0, True, registration=reg_1, num_persons=1)
    _assert_occupied_slots(reg_1, 2)
    _assert_registration_count(dummy_regform, 2)

    create_accompanying_persons_field(0, True, registration=reg_1, num_persons=2)
    _assert_occupied_slots(reg_1, 4)
    _assert_registration_count(dummy_regform, 4)

    reg_2 = create_registration(2)
    _assert_occupied_slots(reg_2, 1)
    _assert_registration_count(dummy_regform, 5)

    dummy_regform.registration_limit = 5
    assert dummy_regform.limit_reached
    dummy_regform.registration_limit = 6
    assert not dummy_regform.limit_reached
