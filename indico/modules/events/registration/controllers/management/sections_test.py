# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.registration.controllers.management.fields import _fill_form_field_with_data
from indico.modules.events.registration.controllers.management.sections import RHRegistrationFormModifySection
from indico.modules.events.registration.models.form_fields import RegistrationFormField
from indico.modules.events.registration.models.items import RegistrationFormSection


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


class TestRHRegistrationFormModifySection:
    def test_delete_section_clears_show_if_field_and_values(self, db, dummy_regform, app_context):
        section_a = RegistrationFormSection(registration_form=dummy_regform, title='Section A',
                                                 is_manager_only=False)
        condition_field = RegistrationFormField(parent=section_a, registration_form=dummy_regform)
        _fill_form_field_with_data(condition_field, {'input_type': 'checkbox', 'title': 'Condition field'})
        db.session.flush()
        section_b = RegistrationFormSection(registration_form=dummy_regform, title='Section B', is_manager_only=False)
        new_field = RegistrationFormField(parent=section_b, registration_form=dummy_regform)
        _fill_form_field_with_data(new_field, {'input_type': 'text', 'title': 'New field'})
        new_field.show_if_id = condition_field.id
        new_field.show_if_values = ['yes']
        db.session.flush()
        with app_context.test_request_context():
            rh = RHRegistrationFormModifySection()
            rh.section = section_b
            rh.regform = dummy_regform
            rh._process_DELETE()
        assert new_field.show_if_id is None
        assert new_field.show_if_values is None
        assert condition_field.condition_for == []

    def test_delete_section_clears_condition_for_links_on_fields(self, db, dummy_regform, app_context):
        section_a = RegistrationFormSection(registration_form=dummy_regform, title='Section A', is_manager_only=False)
        condition_field = RegistrationFormField(parent=section_a, registration_form=dummy_regform)
        _fill_form_field_with_data(condition_field, {'input_type': 'checkbox', 'title': 'Condition field'})
        db.session.flush()
        section_b = RegistrationFormSection(registration_form=dummy_regform, title='Section B', is_manager_only=False)
        new_field = RegistrationFormField(parent=section_b, registration_form=dummy_regform)
        _fill_form_field_with_data(new_field, {'input_type': 'text', 'title': 'New field'})
        new_field.show_if_id = condition_field.id
        new_field.show_if_values = ['yes']
        db.session.flush()
        with app_context.test_request_context():
            rh = RHRegistrationFormModifySection()
            rh.section = section_a
            rh.regform = dummy_regform
            rh._process_DELETE()
        db.session.expire(condition_field, ['condition_for'])
        assert condition_field.condition_for == []
