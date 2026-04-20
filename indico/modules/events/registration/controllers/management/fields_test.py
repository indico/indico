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


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


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
            schema.load({'input_type': last_name_field.input_type, 'title': first_name_field.title,
                         'internal_name': last_name_field.internal_name})
        assert exc_info.value.messages == {'title': 'There is already a field in this section with the same title.'}

    def test_update_title_of_disabled_field(self, dummy_regform):
        pd_section = dummy_regform.sections[0]
        position_field = next((field for field in pd_section.fields
                               if field.personal_data_type == PersonalDataType.position), None)
        disabled_field = RegistrationFormField(parent=pd_section, registration_form=dummy_regform, is_enabled=False,
                                               id=1337)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': disabled_field})
        assert schema.load({'input_type': 'text', 'title': position_field.title,
                            'internal_name': position_field.internal_name})

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

    @pytest.mark.parametrize('internal_name', ('internal name', 'InternalName', 'internal.name', 'internal_name', ''))
    def test_update_internal_name_with_not_allowed_chars(self, dummy_regform, internal_name):
        pd_section = dummy_regform.sections[0]
        new_field = RegistrationFormField(parent=pd_section, registration_form=dummy_regform)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_field})
        with pytest.raises(ValidationError) as exc_info:
            schema.load({'input_type': 'text', 'title': 'New field', 'internal_name': internal_name})
        assert exc_info.value.messages == {'internal_name': ['String does not match expected pattern.']}

    @pytest.mark.parametrize('internal_name', ('alt-position', None))
    def test_update_internal_name_of_personal_data_field(self, dummy_regform, internal_name):
        pd_section = dummy_regform.sections[0]
        position_field = next((field for field in pd_section.fields
                               if field.personal_data_type == PersonalDataType.position), None)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': position_field})
        with pytest.raises(ValidationError) as exc_info:
            assert schema.load({'input_type': 'text', 'title': position_field.title, 'internal_name': internal_name})
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

    def test_internal_name_with_different_input_type_on_other_regform(self, db, create_regform, dummy_regform):
        other_form = create_regform(dummy_regform.event, title='Other Form')
        pd_section = dummy_regform.sections[0]
        # Disable the title field on dummy_regform to be able to add another title field but with different type
        title_field = next((field for field in pd_section.fields
                            if field.personal_data_type == PersonalDataType.title), None)
        title_field.is_enabled = False
        db.session.flush()
        new_section = RegistrationFormSection(registration_form=dummy_regform, title='New Section',
                                              is_manager_only=False)
        new_field = RegistrationFormField(parent=new_section, registration_form=dummy_regform, title='test',
                                          input_type='text')
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_field})
        with pytest.raises(ValidationError) as exc_info:
            schema.load({'input_type': 'text', 'title': 'test', 'internal_name': 'title'})
        assert exc_info.value.messages == {
            'internal_name': [f'The field "Title" with the same internal name on form '
                              f'"{other_form.title}" uses a different input type which is not allowed.']
        }
        other_form.is_deleted = True
        db.session.flush()
        assert schema.load({'input_type': 'text', 'title': 'text', 'internal_name': 'title'})

    def test_internal_name_with_different_input_type_on_other_event(self, db, create_event, dummy_regform,
                                                                    create_regform):
        # create field in dummy event
        new_field = RegistrationFormField(parent=dummy_regform.sections[0], registration_form=dummy_regform,
                                          title='test', input_type='text', internal_name='test')
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_field})
        schema.load({'input_type': 'text', 'title': 'test', 'internal_name': 'test'})
        db.session.flush()
        # create field in another event
        other_event = create_event()
        other_form = create_regform(other_event, title='Other Form')
        other_field = RegistrationFormField(parent=other_form.sections[0], registration_form=other_form,
                                            title='test', input_type='checkbox')
        schema = GeneralFieldDataSchema(context={'regform': other_form, 'field': other_field})
        schema.load({'input_type': 'checkbox', 'title': 'test', 'internal_name': 'test'})
