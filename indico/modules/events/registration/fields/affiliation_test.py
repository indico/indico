# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from marshmallow import ValidationError

from indico.core import signals
from indico.modules.events.registration.fields.affiliation import AffiliationMode
from indico.modules.events.registration.models.form_fields import RegistrationFormField
from indico.modules.users.models.affiliations import Affiliation


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


@pytest.fixture
def affiliation_field(dummy_regform):
    field = RegistrationFormField(
        input_type='affiliation',
        title='Affiliation',
        parent=dummy_regform.sections[0],
        registration_form=dummy_regform,
    )
    field.versioned_data = {}
    return field


@pytest.mark.parametrize(
    ('is_required', 'mode', 'value', 'error'),
    (
        (True, AffiliationMode.both, {'id': None, 'text': ''}, 'This field cannot be empty'),
        (False, AffiliationMode.predefined, {'id': None, 'text': 'CERN'},
         'Please select an affiliation from the list'),
        (False, AffiliationMode.custom, {'id': 123, 'text': 'CERN'}, 'Please enter a custom affiliation'),
    ),
)
def test_affiliation_validate_errors(affiliation_field, is_required, mode, value, error):
    affiliation_field.is_required = is_required
    affiliation_field.data = {'affiliation_mode': mode}
    validator = affiliation_field.field_impl.get_validators(None)
    with pytest.raises(ValidationError, match=error):
        validator(value)


def test_affiliation_process_form_data_sets_canonical_text(db, affiliation_field, dummy_reg):
    affiliation_field.data = {'affiliation_mode': AffiliationMode.both}
    affiliation = Affiliation(name='CERN')
    db.session.add(affiliation)
    db.session.flush()
    rv = affiliation_field.field_impl.process_form_data(dummy_reg, {'id': affiliation.id, 'text': 'Wrong'})
    assert rv['data'] == {'id': affiliation.id, 'text': affiliation.name}


def test_affiliation_process_form_data_invalid_id_raises(affiliation_field, dummy_reg):
    affiliation_field.data = {'affiliation_mode': AffiliationMode.both}
    with pytest.raises(ValidationError, match='Invalid affiliation'):
        affiliation_field.field_impl.process_form_data(dummy_reg, {'id': 999999, 'text': 'CERN'})


def test_affiliation_process_form_data_applies_signal_filters(db, affiliation_field, dummy_reg):
    affiliation_field.data = {'affiliation_mode': AffiliationMode.both}
    affiliation = Affiliation(name='CERN')
    db.session.add(affiliation)
    db.session.flush()
    signal_data = {}

    def _get_filters(sender, context, **kwargs):
        signal_data['sender'] = sender
        signal_data['context'] = context
        return [Affiliation.name == 'Not CERN']

    with signals.affiliations.get_affiliation_filters.connected_to(_get_filters):
        with pytest.raises(ValidationError, match='Invalid affiliation'):
            affiliation_field.field_impl.process_form_data(dummy_reg, {'id': affiliation.id, 'text': 'CERN'})

    assert signal_data['sender'] is affiliation_field.field_impl
    assert signal_data['context']['event'] == affiliation_field.registration_form.event
    assert signal_data['context']['registration_form'] == affiliation_field.registration_form
    assert signal_data['context']['registration'] == dummy_reg
