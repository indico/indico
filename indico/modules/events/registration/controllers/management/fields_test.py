# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from marshmallow import ValidationError

from indico.modules.formify.controllers.management.fields import GeneralFieldDataSchema
from indico.modules.formify.models.form_fields import RegistrationFormField
from indico.modules.formify.models.items import PersonalDataType, RegistrationFormSection


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


class TestGeneralFieldDataSchema:
    def test_add_new_field_with_same_title_in_same_section(self, dummy_regform):
        pd_section = dummy_regform.sections[0]
        first_name_field = next((field for field in pd_section.fields
                                 if field.personal_data_type == PersonalDataType.first_name), None)
        new_field = RegistrationFormField(parent=pd_section, registration_form=dummy_regform)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_field})
        with pytest.raises(ValidationError) as exc_info:
            schema.load({'input_type': 'text', 'title': first_name_field.title})
        assert exc_info.value.messages == {'title': 'There is already a field in this section with the same title.'}

    def test_modify_field_with_same_title_in_same_section(self, dummy_regform):
        pd_section = dummy_regform.sections[0]
        first_name_field = next((field for field in pd_section.fields
                                 if field.personal_data_type == PersonalDataType.first_name), None)
        last_name_field = next((field for field in pd_section.fields
                                if field.personal_data_type == PersonalDataType.last_name), None)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': last_name_field})
        with pytest.raises(ValidationError) as exc_info:
            schema.load({'input_type': last_name_field.input_type, 'title': first_name_field.title})
        assert exc_info.value.messages == {'title': 'There is already a field in this section with the same title.'}

    def test_update_title_of_disabled_field(self, dummy_regform):
        pd_section = dummy_regform.sections[0]
        position_field = next((field for field in pd_section.fields
                               if field.personal_data_type == PersonalDataType.position), None)
        disabled_field = RegistrationFormField(parent=pd_section, registration_form=dummy_regform, is_enabled=False,
                                               id=1337)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': disabled_field})
        assert schema.load({'input_type': 'text', 'title': position_field.title})

    def test_add_new_field_with_same_title_but_disabled(self, db, dummy_regform):
        pd_section = dummy_regform.sections[0]
        affiliation_field = next((field for field in pd_section.fields
                                    if field.personal_data_type == PersonalDataType.affiliation), None)
        affiliation_field.is_enabled = False
        db.session.flush()
        new_affiliation_field = RegistrationFormField(parent=pd_section, registration_form=dummy_regform)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_affiliation_field})
        assert schema.load({'input_type': 'text', 'title': affiliation_field.title})

    def test_add_new_field_with_same_title_in_other_section(self, dummy_regform):
        pd_section = dummy_regform.sections[0]
        first_name_field = next((field for field in pd_section.fields
                                 if field.personal_data_type == PersonalDataType.first_name), None)
        new_section = RegistrationFormSection(
            registration_form=dummy_regform, title='New Section', is_manager_only=False
        )
        new_field = RegistrationFormField(parent=new_section, registration_form=dummy_regform)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_field})
        assert schema.load({'input_type': 'text', 'title': first_name_field.title})
