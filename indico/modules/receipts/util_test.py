# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.registration.controllers.management.fields import _fill_form_field_with_data
from indico.modules.events.registration.models.form_fields import RegistrationFormField
from indico.modules.events.registration.models.items import RegistrationFormSection
from indico.modules.events.registration.models.registrations import RegistrationData
from indico.modules.receipts.util import (compile_jinja_code, get_dummy_preview_data, get_preview_placeholders,
                                          get_safe_template_context)


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


@pytest.mark.usefixtures('app_context')
@pytest.mark.parametrize(('name', 'key', 'access'), (
    ('billing-address', 'billing_address', '.billing_address'),
    ('items', 'items', "['items']"),
    ('123', '123', "['123']"),
))
def test_named_field_lookup(name, key, access):
    from indico.modules.receipts.schemas import RegistrationDataSchema

    context = get_dummy_preview_data([])
    registration = context['registration']
    field = registration['field_data_by_name']['preferred_energy_source']
    field['internal_name'] = name
    registration = RegistrationDataSchema().load(RegistrationDataSchema().dump(registration))
    context['registration'] = registration
    assert registration['field_data_by_name'][key] == field
    assert registration['custom_data'] == {key: 'Zero-Point-Module'}
    expression = f'registration.field_data_by_name{access}.friendly_value'
    assert compile_jinja_code('{{ ' + expression + ' }}', context) == 'Zero-Point-Module'
    placeholders = dict(get_preview_placeholders(context))
    assert {key for key in placeholders if key.startswith(f'registration.field_data_by_name{access}.')} == {expression}
    assert 'registration.field_data[0].config' in placeholders
    assert 'registration.field_data[0].raw_value' in placeholders
    assert compile_jinja_code(
        '{{ registration.field_data_by_name' + access + '.config.item_type }}', context
    ) == 'dropdown'
    expression = f'registration.custom_data{access}'
    assert compile_jinja_code('{{ ' + expression + ' }}', context) == 'Zero-Point-Module'
    assert expression in placeholders


@pytest.mark.usefixtures('app_context')
def test_dummy_named_fields():
    context = get_dummy_preview_data([])
    registration = context['registration']
    assert registration['field_data_by_name']['first_name']['friendly_value'] == 'Jack'
    assert registration['field_data_by_name']['preferred_energy_source']['friendly_value'] == 'Zero-Point-Module'
    assert registration['custom_data'] == {'preferred_energy_source': 'Zero-Point-Module'}
    assert compile_jinja_code(
        "{% if 'missing' in registration.field_data_by_name %}present{% else %}absent{% endif %}", context
    ) == 'absent'


@pytest.mark.parametrize('excluded', ('disabled', 'deleted', 'missing', 'unnamed'))
def test_named_fields_from_registration(db, dummy_event, dummy_reg, dummy_regform, excluded):
    section = RegistrationFormSection(registration_form=dummy_regform, title='Details')
    for name, value in (('billing-address', 'Somewhere'), ('other', 'Other value')):
        field = RegistrationFormField(parent=section, registration_form=dummy_regform, internal_name=name)
        _fill_form_field_with_data(field, {'input_type': 'text', 'title': f'Display title for {name}'})
        if name == 'other':
            if excluded == 'disabled':
                field.is_enabled = False
            elif excluded == 'deleted':
                field.is_deleted = True
            elif excluded == 'unnamed':
                field.internal_name = None
            elif excluded == 'missing':
                continue
        dummy_reg.data.append(RegistrationData(field_data=field.current_data, data=value))
    db.session.flush()
    registration = get_safe_template_context(dummy_event, dummy_reg, {})['registration']
    named = registration['field_data_by_name']
    assert named['billing_address']['friendly_value'] == 'Somewhere'
    assert named['billing_address']['internal_name'] == 'billing-address'
    assert named['billing_address'] == registration['field_data'][0]
    assert set(named) == {'billing_address'}
    assert len(registration['field_data']) == (2 if excluded == 'unnamed' else 1)
    assert registration['custom_data'] == {'billing_address': 'Somewhere'}


def test_personal_fields_excluded_from_custom_data(db, dummy_event, dummy_reg, dummy_regform):
    field = next(field for field in dummy_regform.active_fields if field.internal_name == 'first-name')
    dummy_reg.data.append(RegistrationData(field_data=field.current_data, data='Jane'))
    db.session.flush()
    registration = get_safe_template_context(dummy_event, dummy_reg, {})['registration']
    assert registration['field_data_by_name']['first_name']['friendly_value'] == 'Jane'
    assert registration['personal_data']['first_name'] == 'Jane'
    assert registration['custom_data'] == {}
