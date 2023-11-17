# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.designer.placeholders import (RegistrationAccompanyingPersonsAbbrevPlaceholder,
                                                  RegistrationAccompanyingPersonsCountPlaceholder,
                                                  RegistrationAccompanyingPersonsPlaceholder)
from indico.modules.events.registration.models.form_fields import RegistrationFormField
from indico.modules.events.registration.models.items import RegistrationFormSection
from indico.modules.events.registration.models.registrations import RegistrationData


pytest_plugins = ('indico.modules.events.registration.testing.fixtures',)


def _id(n):
    assert 0 <= n < 10000000
    return f'{n:08d}-0000-0000-0000-000000000000'


def _create_accompanying_persons(n):
    return [{'id': _id(i), 'firstName': 'Guinea', 'lastName': 'Pig'} for i in range(n)]


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


def test_accompanying_persons_placeholder(dummy_reg, create_accompanying_persons_field):
    create_accompanying_persons_field(2, False, registration=dummy_reg, num_persons=2)

    assert RegistrationAccompanyingPersonsCountPlaceholder.render(dummy_reg) == '2'
    assert RegistrationAccompanyingPersonsPlaceholder.render(dummy_reg) == 'Guinea PIG, Guinea PIG'
    assert RegistrationAccompanyingPersonsAbbrevPlaceholder.render(dummy_reg) == 'G. PIG, G. PIG'
