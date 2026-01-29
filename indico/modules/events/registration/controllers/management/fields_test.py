# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from marshmallow import ValidationError

from indico.modules.events.registration.controllers.management.fields import GeneralFieldDataSchema
from indico.modules.events.registration.models.form_fields import RegistrationFormField
from indico.modules.events.registration.models.items import PersonalDataType, RegistrationFormSection


class TestGeneralFieldDataSchema:

    # title tests

    def test_new_field_with_same_title_in_same_section(self, dummy_regform):
        pd_section = dummy_regform.sections[0]
        first_name_field = next((field for field in pd_section.fields
                                 if field.personal_data_type == PersonalDataType.first_name), None)
        new_field = RegistrationFormField(parent=pd_section, registration_form=dummy_regform)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_field})
        with pytest.raises(ValidationError) as exc_info:
            schema.load({'input_type': 'text', 'title': first_name_field.title})
        assert exc_info.value.messages == {'title': 'There is already a field in this section with the same title.'}

    def test_update_field_with_same_title_in_same_section(self, dummy_regform):
        pd_section = dummy_regform.sections[0]
        first_name_field = next((field for field in pd_section.fields
                                 if field.personal_data_type == PersonalDataType.first_name), None)
        last_name_field = next((field for field in pd_section.fields
                                if field.personal_data_type == PersonalDataType.last_name), None)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': last_name_field})
        with pytest.raises(ValidationError) as exc_info:
            schema.load({'input_type': last_name_field.input_type, 'title': first_name_field.title})
        assert exc_info.value.messages == {'title': 'There is already a field in this section with the same title.'}

    def test_new_field_with_same_title_but_disabled(self, db, dummy_regform):
        pd_section = dummy_regform.sections[0]
        affiliation_field = next((field for field in pd_section.fields
                                    if field.personal_data_type == PersonalDataType.affiliation), None)
        affiliation_field.is_enabled = False
        db.session.flush()
        new_affiliation_field = RegistrationFormField(parent=pd_section, registration_form=dummy_regform)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_affiliation_field})
        assert schema.load({'input_type': 'text', 'title': affiliation_field.title})

    def test_new_field_with_same_title_in_other_section(self, dummy_regform):
        pd_section = dummy_regform.sections[0]
        first_name_field = next((field for field in pd_section.fields
                                 if field.personal_data_type == PersonalDataType.first_name), None)
        new_section = RegistrationFormSection(
            registration_form=dummy_regform, title='New Section', is_manager_only=False
        )
        new_field = RegistrationFormField(parent=new_section, registration_form=dummy_regform)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_field})
        assert schema.load({'input_type': 'text', 'title': first_name_field.title})

    # internal_name tests

    def test_new_field_with_same_internal_name(self, dummy_regform):
        pd_section = dummy_regform.sections[0]
        position_field = next((field for field in pd_section.fields
                               if field.personal_data_type == PersonalDataType.position), None)
        new_field = RegistrationFormField(parent=pd_section, registration_form=dummy_regform)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_field})
        with pytest.raises(ValidationError) as exc_info:
            schema.load({'input_type': 'text', 'title': 'New field', 'internal_name': position_field.internal_name})
        assert exc_info.value.messages == {'internal_name': [f'The field "{position_field.title}" on this form '
                                                             f'has the same internal name.']}

    def test_update_internal_name_with_whitespaces(self, dummy_regform):
        pd_section = dummy_regform.sections[0]
        new_field = RegistrationFormField(parent=pd_section, registration_form=dummy_regform)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_field})
        with pytest.raises(ValidationError) as exc_info:
            schema.load({'input_type': 'text', 'title': 'New field', 'internal_name': ' new_field '})
        assert exc_info.value.messages == {'internal_name': 'Leading and trailing whitespaces are not allowed.'}

    def test_update_internal_name_of_personal_data_field(self, dummy_regform):
        pd_section = dummy_regform.sections[0]
        position_field = next((field for field in pd_section.fields
                               if field.personal_data_type == PersonalDataType.position), None)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': position_field})
        with pytest.raises(ValidationError) as exc_info:
            assert schema.load({'input_type': 'text', 'title': position_field.title, 'internal_name': 'alt_position'})
        assert exc_info.value.messages == {'internal_name': 'Changing internal name for personal data field '
                                                            'is not allowed.'}

    def test_update_internal_name_of_disabled_field(self, dummy_regform):
        pd_section = dummy_regform.sections[0]
        position_field = next((field for field in pd_section.fields
                               if field.personal_data_type == PersonalDataType.position), None)
        disabled_field = RegistrationFormField(parent=pd_section, registration_form=dummy_regform, is_enabled=False)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': disabled_field})
        assert schema.load({'input_type': 'text', 'title': 'Disabled field',
                            'internal_name': position_field.internal_name})

    def test_new_field_with_same_internal_name_but_disabled(self, db, dummy_regform):
        pd_section = dummy_regform.sections[0]
        position_field = next((field for field in pd_section.fields
                               if field.personal_data_type == PersonalDataType.position), None)
        position_field.is_enabled = False
        db.session.flush()
        new_position_field = RegistrationFormField(parent=pd_section, registration_form=dummy_regform)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_position_field})
        assert schema.load({'input_type': 'text', 'title': position_field.title,
                            'internal_name': position_field.internal_name})
