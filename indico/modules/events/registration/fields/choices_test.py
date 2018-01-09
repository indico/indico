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

from copy import deepcopy

import pytest

from indico.modules.events.registration.fields.choices import _hashable_choice
from indico.modules.events.registration.models.form_fields import RegistrationFormField
from indico.modules.events.registration.models.registrations import RegistrationData


def _id(n):
    assert 0 <= n < 10
    return '{}0000000-0000-0000-0000-000000000000'.format(n)


@pytest.fixture
def multi_choice_field():
    field = RegistrationFormField(input_type='multi_choice')
    field.versioned_data = {
        'choices': [
            {'id': _id(1), 'places_limit': 0, 'is_billable': False, 'price': 0},
            {'id': _id(2), 'places_limit': 0, 'is_billable': False, 'price': 0},
            {'id': _id(3), 'places_limit': 0, 'is_billable': True, 'price': 10}
        ]
    }
    return field


def _update_data(data, changes):
    data = dict(deepcopy(data))
    refs = {x['id']: x for x in data['choices']}
    for id_, item_changes in changes.iteritems():
        if id_ not in refs:
            entry = {'id': id_, 'places_limit': 0, 'is_billable': False, 'price': 0}
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
    combined = new_choices[:2] + [old_choices[2]] + [new_choices[-1]]
    _assert_same_choices(rv['field_data'].versioned_data['choices'], combined)


def test_multi_choice_field_process_form_data_price_change_deselected(multi_choice_field):
    # reg linked to old version, a currently selected item had its price changed and another changed
    # item was deselected.
    # field data should be upgraded to a new version containing both the new items and the old-priced one
    multi_choice_field.versioned_data = _update_data(multi_choice_field.versioned_data,
                                                     {_id(2): {'is_billable': True, 'price': 100},
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
    combined = [old_choices[-1]] + new_choices[:-1]
    _assert_same_choices(rv['field_data'].versioned_data['choices'], combined)
    # now we re-check the previously deselected option and should get the NEW price
    form_data = {_id(2): 1, _id(3): 1}
    rv = multi_choice_field.field_impl.process_form_data(None, form_data, new_data)
    assert RegistrationData(**rv).price == 510
