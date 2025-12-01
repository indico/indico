# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from copy import deepcopy
from datetime import date

import pytest
from marshmallow import ValidationError

from indico.modules.events.registration.fields.choices import MultiChoiceSetupSchema, _hashable_choice
from indico.modules.events.registration.models.form_fields import RegistrationFormField
from indico.modules.events.registration.models.registrations import RegistrationData


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


def _id(n):
    assert 0 <= n < 10
    return f'{n}0000000-0000-0000-0000-000000000000'


@pytest.fixture
def multi_choice_field():
    field = RegistrationFormField(input_type='multi_choice')
    field.versioned_data = {
        'choices': [
            {'id': _id(1), 'places_limit': 0, 'price': 0},
            {'id': _id(2), 'places_limit': 0, 'price': 0},
            {'id': _id(3), 'places_limit': 0, 'price': 10}
        ]
    }
    field.data = {
        'captions': {
            _id(1): 'Option 1',
            _id(2): 'Option 2',
            _id(3): 'Option 3',
        },
        'max_choices': None
    }
    return field


@pytest.fixture
def dummy_accommodation_field(dummy_regform):
    return RegistrationFormField(
        input_type='accommodation',
        title='Field',
        parent=dummy_regform.sections[0],
        registration_form=dummy_regform,
        data={
            'arrival_date_from': '2025-11-20',
            'arrival_date_to': '2025-11-22',
            'departure_date_from': '2025-11-22',
            'departure_date_to': '2025-11-24',
            'captions': {
                _id(0): 'No Acc',
                _id(1): 'Valid Acc',
                _id(2): 'Disabled Acc',
            },
        },
        versioned_data={
            'choices': [
                {
                    'id': _id(0),
                    'price': 0,
                    'is_enabled': True,
                    'places_limit': 0,
                    'is_no_accommodation': True,
                },
                {
                    'id': _id(1),
                    'price': 0,
                    'is_enabled': True,
                    'places_limit': 0,
                    'is_no_accommodation': False,
                },
                {
                    'id': _id(2),
                    'price': 0,
                    'is_enabled': False,
                    'places_limit': 0,
                    'is_no_accommodation': False,
                },
            ]
        },
    )


def _update_data(data, changes):
    data = dict(deepcopy(data))
    refs = {x['id']: x for x in data['choices']}
    for id_, item_changes in changes.items():
        if id_ not in refs:
            entry = {'id': id_, 'places_limit': 0, 'price': 0}
            entry.update(item_changes)
            data['choices'].append(entry)
        elif item_changes is None:
            data['choices'].remove(refs[id_])
        else:
            refs[id_].update(item_changes)
    return data


def _assert_same_choices(a, b):
    __tracebackhide__ = True
    assert {_hashable_choice(x) for x in a} == {_hashable_choice(x) for x in b}


def test_multi_choice_field_process_form_data_no_old(multi_choice_field):
    # no existing data
    form_data = {_id(1): 1, _id(2): 1}
    expected = {'field_data': multi_choice_field.current_data, 'data': form_data}
    assert multi_choice_field.field_impl.process_form_data(None, form_data) == expected


def test_multi_choice_field_process_form_data_current_version(multi_choice_field):
    # nothing changed
    old_data = RegistrationData(field_data=multi_choice_field.current_data, data={_id(1): 1, _id(2): 1})
    form_data = {_id(1): 1, _id(2): 1}
    assert multi_choice_field.field_impl.process_form_data(None, form_data, old_data) == {}


def test_multi_choice_field_process_form_data_old_version(multi_choice_field):
    # reg linked to old version, price changed in new version, nothing changed
    # in this case everything should remain linked to the old version
    old_version = multi_choice_field.current_data
    old_data = RegistrationData(field_data=old_version, data={_id(2): 1, _id(3): 1})
    multi_choice_field.versioned_data = _update_data(multi_choice_field.versioned_data, {_id(3): {'price': 1000}})
    form_data = {_id(2): 1, _id(3): 1}
    assert multi_choice_field.field_impl.process_form_data(None, form_data, old_data) == {}


def test_multi_choice_field_process_form_data_item_removed(multi_choice_field):
    # reg linked to old version, one selected item removed from there
    # in this case everything should remain linked to the old version
    old_version = multi_choice_field.current_data
    old_data = RegistrationData(field_data=old_version, data={_id(1): 1, _id(2): 1})
    multi_choice_field.versioned_data = _update_data(multi_choice_field.versioned_data, {_id(1): None})
    form_data = {_id(1): 1, _id(2): 1}
    assert multi_choice_field.field_impl.process_form_data(None, form_data, old_data) == {}


def test_multi_choice_field_process_form_data_item_removed_deselected(multi_choice_field):
    # reg linked to old version, one selected item removed from there and deselected
    # since all other items are available in the latest version we upgrade to it
    old_version = multi_choice_field.current_data
    old_data = RegistrationData(field_data=old_version, data={_id(1): 1, _id(2): 1})
    multi_choice_field.versioned_data = _update_data(multi_choice_field.versioned_data, {_id(1): None})
    form_data = {_id(2): 1}
    rv = multi_choice_field.field_impl.process_form_data(None, form_data, old_data)
    assert rv['field_data'] == multi_choice_field.current_data
    assert rv['data'] == form_data


def test_multi_choice_field_process_form_data_only_new(multi_choice_field):
    # reg linked to old version, but all old items deselected
    # field data should be upgraded to the current version
    old_version = multi_choice_field.current_data
    old_data = RegistrationData(field_data=old_version, data={_id(1): 1, _id(2): 1})
    multi_choice_field.versioned_data = _update_data(multi_choice_field.versioned_data, {_id(1): None, _id(4): {}})
    form_data = {_id(4): 1}
    rv = multi_choice_field.field_impl.process_form_data(None, form_data, old_data)
    assert rv['field_data'] == multi_choice_field.current_data
    assert rv['data'] == form_data


def test_multi_choice_field_process_form_data_mixed(multi_choice_field):
    # reg linked to old version, a currently selected item was deleted and a new item is selected
    # field data should be upgraded to a new version containing both the new items and the deleted one
    old_version = multi_choice_field.current_data
    old_data = RegistrationData(field_data=old_version, data={_id(1): 1})
    multi_choice_field.versioned_data = _update_data(multi_choice_field.versioned_data, {_id(1): None, _id(4): {}})
    form_data = {_id(1): 1, _id(4): 1}
    rv = multi_choice_field.field_impl.process_form_data(None, form_data, old_data)
    assert rv['field_data'] not in {multi_choice_field.current_data, old_version}
    assert rv['data'] == form_data
    combined = multi_choice_field.versioned_data['choices'] + [old_version.versioned_data['choices'][0]]
    _assert_same_choices(rv['field_data'].versioned_data['choices'], combined)


def test_multi_choice_field_process_form_data_mixed_price_change(multi_choice_field):
    # reg linked to old version, a currently selected item had its price changed and a new item is selected
    # field data should be upgraded to a new version containing both the new items and the old-priced one
    old_version = multi_choice_field.current_data
    old_data = RegistrationData(field_data=old_version, data={_id(3): 1})
    multi_choice_field.versioned_data = _update_data(multi_choice_field.versioned_data, {_id(3): {'price': 1000},
                                                                                         _id(4): {}})
    form_data = {_id(3): 1, _id(4): 1}
    rv = multi_choice_field.field_impl.process_form_data(None, form_data, old_data)
    assert rv['field_data'] not in {multi_choice_field.current_data, old_version}
    assert rv['data'] == form_data
    old_choices = old_version.versioned_data['choices']
    new_choices = multi_choice_field.versioned_data['choices']
    combined = [*new_choices[:2], old_choices[2], new_choices[-1]]
    _assert_same_choices(rv['field_data'].versioned_data['choices'], combined)


def test_multi_choice_field_process_form_data_price_change_deselected(multi_choice_field):
    # reg linked to old version, a currently selected item had its price changed and another changed
    # item was deselected.
    # field data should be upgraded to a new version containing both the new items and the old-priced one
    multi_choice_field.versioned_data = _update_data(multi_choice_field.versioned_data,
                                                     {_id(2): {'price': 100},
                                                      _id(3): {'price': 500}})
    old_version = multi_choice_field.current_data
    old_data = RegistrationData(field_data=old_version, data={_id(2): 1, _id(3): 1})
    assert old_data.price == 600
    multi_choice_field.versioned_data = _update_data(multi_choice_field.versioned_data, {_id(2): {'price': 10},
                                                                                         _id(3): {'price': 50}})
    form_data = {_id(3): 1}
    rv = multi_choice_field.field_impl.process_form_data(None, form_data, old_data)
    assert rv['field_data'] not in {multi_choice_field.current_data, old_version}
    assert rv['data'] == form_data
    new_data = RegistrationData(**rv)
    assert new_data.price == 500
    old_choices = old_version.versioned_data['choices']
    new_choices = multi_choice_field.versioned_data['choices']
    combined = [old_choices[-1], *new_choices[:-1]]
    _assert_same_choices(rv['field_data'].versioned_data['choices'], combined)
    # now we re-check the previously deselected option and should get the NEW price
    form_data = {_id(2): 1, _id(3): 1}
    rv = multi_choice_field.field_impl.process_form_data(None, form_data, new_data)
    assert RegistrationData(**rv).price == 510


def test_multi_choice_field_validate_max_choices(multi_choice_field):
    def run_validators(validators, value):
        for v in validators:
            v(value)

    validators = multi_choice_field.field_impl.get_validators(None)
    run_validators(validators, {})
    run_validators(validators, {_id(1): 1, _id(2): 1})

    multi_choice_field.data['max_choices'] = 1
    run_validators(validators, {_id(1): 1})
    with pytest.raises(ValidationError, match='At most 1 option can be selected'):
        run_validators(validators, {_id(1): 1, _id(2): 1})

    multi_choice_field.data['max_choices'] = 2
    run_validators(validators, {_id(1): 1, _id(2): 1})
    with pytest.raises(ValidationError, match='At most 2 options can be selected'):
        run_validators(validators, {_id(1): 1, _id(2): 1, _id(3): 1})


@pytest.mark.parametrize(('max_choices', 'n_choices', 'error'), (
    (-3, 2, 'Maximum choices must be greater than 0'),
    (None, 2, None),
    (1, 2, None),
    (2, 2, None),
    (4, 3, 'Value must not be greater than the total number of choices')
))
def test_multi_choice_setup_schema_max_choices_validation(max_choices, n_choices, error):
    def _choice(n):
        return {
            'id': _id(n),
            'caption': f'Option {n}',
            'is_enabled': True,
        }

    schema = MultiChoiceSetupSchema()
    choices = [_choice(n) for n in range(n_choices)]
    data = {'max_choices': max_choices, 'choices': choices}

    if error:
        with pytest.raises(ValidationError, match=error):
            schema.load(data)
    else:
        schema.load(data)


@pytest.mark.parametrize(('value', 'error'), (
    # valid no accommodation
    ({'choice': _id(0), 'isNoAccommodation': True}, None),
    # invalid value for isNoAccommodation
    ({'choice': _id(0), 'isNoAccommodation': False}, 'Invalid data'),
    ({'choice': _id(1), 'isNoAccommodation': True}, 'Invalid data'),
    # XXX: isNoAccommodation defaults to False so we omit it for readability
    # invalid option
    ({'choice': _id(9)}, 'Invalid choice'),
    # disabled option
    ({'choice': _id(2)}, 'Invalid choice'),
    # missing dates
    ({'choice': _id(1)}, 'Arrival/departure date is missing'),
    ({'choice': _id(1), 'arrivalDate': '2025-11-20'}, 'Arrival/departure date is missing'),
    ({'choice': _id(1), 'departureDate': '2025-11-22'}, 'Arrival/departure date is missing'),
    # valid accommodation
    ({'choice': _id(1), 'arrivalDate': '2025-11-20', 'departureDate': '2025-11-22'}, None),
    ({'choice': _id(1), 'arrivalDate': '2025-11-22', 'departureDate': '2025-11-22'}, None),
    # nonsense dates / outside range
    ({'choice': _id(1), 'arrivalDate': '2025-11-22', 'departureDate': '2025-11-21'},
     "Arrival date can't be set after the departure date."),
    ({'choice': _id(1), 'arrivalDate': '2025-11-01', 'departureDate': '2025-11-22'},
     'Arrival date is not within the required range.'),
    ({'choice': _id(1), 'arrivalDate': '2025-11-20', 'departureDate': '2025-12-01'},
     'Departure date is not within the required range.'),
))
@pytest.mark.usefixtures('request_context')  # to avoid lazy strings in errors
def test_accommodation_validators(dummy_accommodation_field, value, error):
    validators = dummy_accommodation_field.field_impl.get_validators(None)

    def _validate(value):
        __tracebackhide__ = True
        for validator in validators:
            validator(value)

    # the validator takes the data as returned vy the AccommodationSchema.
    # since we don't use it here, we need to do the relevant parts of it ourselves
    value.setdefault('isNoAccommodation', False)
    if arrival_date := value.get('arrivalDate'):
        value['arrivalDate'] = date.fromisoformat(arrival_date)
    if departure_date := value.get('departureDate'):
        value['departureDate'] = date.fromisoformat(departure_date)

    if error is None:
        _validate(value)
    else:
        with pytest.raises(ValidationError) as exc_info:
            _validate(value)
        assert exc_info.value.messages == [error]
