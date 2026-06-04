# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from marshmallow import ValidationError
from werkzeug.exceptions import BadRequest

from indico.modules.events.registration.controllers.management.fields import (GeneralFieldDataSchema,
                                                                              RHRegistrationFormModifyField,
                                                                              RHRegistrationFormToggleFieldState,
                                                                              _fill_form_field_with_data)
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

    def test_new_field_with_empty_internal_name(self, dummy_regform):
        pd_section = dummy_regform.sections[0]
        new_field = RegistrationFormField(parent=pd_section, registration_form=dummy_regform)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_field})
        assert schema.load({'input_type': 'text', 'title': 'New field'})

    def test_multiple_fields_with_empty_internal_name(self, db, dummy_regform):
        pd_section = dummy_regform.sections[0]
        new_field_1 = RegistrationFormField(parent=pd_section, registration_form=dummy_regform)
        _fill_form_field_with_data(new_field_1, {'input_type': 'text', 'title': 'New field 1'})
        db.session.flush()
        new_field_2 = RegistrationFormField(parent=pd_section, registration_form=dummy_regform)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_field_2})
        assert schema.load({'input_type': 'text', 'title': 'New field 2'})

    def test_new_field_with_unique_internal_name(self, dummy_regform):
        pd_section = dummy_regform.sections[0]
        new_field = RegistrationFormField(parent=pd_section, registration_form=dummy_regform)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_field})
        assert schema.load({'input_type': 'text', 'title': 'New field', 'internal_name': 'unique-internal-name'})

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

    # show_if_field tests

    def test_show_if_field_not_allowed_for_manager_only_section_field(self, db, dummy_regform):
        section = RegistrationFormSection(registration_form=dummy_regform, title='Section',
                                                  is_manager_only=False)
        condition_field = RegistrationFormField(parent=section, registration_form=dummy_regform)
        _fill_form_field_with_data(condition_field, {'input_type': 'checkbox', 'title': 'Condition field'})
        db.session.flush()
        manager_section = RegistrationFormSection(registration_form=dummy_regform, title='Manager section',
                                                  is_manager_only=True)
        new_field = RegistrationFormField(parent=manager_section, registration_form=dummy_regform)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_field})
        with pytest.raises(ValidationError) as exc_info:
            schema.load({'input_type': 'text', 'title': 'Manager field',
                         'show_if_field_id': condition_field.id, 'show_if_field_values': ['yes']})
        assert exc_info.value.messages == {'show_if_field_id': ['Manager-only fields cannot be conditionally shown']}

    def test_show_if_field_self_reference(self, db, dummy_regform):
        section = RegistrationFormSection(registration_form=dummy_regform, title='Section', is_manager_only=False)
        field = RegistrationFormField(parent=section, registration_form=dummy_regform)
        _fill_form_field_with_data(field, {'input_type': 'checkbox', 'title': 'Field'})
        db.session.flush()
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': field})
        with pytest.raises(ValidationError) as exc_info:
            schema.load({'input_type': 'checkbox', 'title': 'Field',
                         'show_if_field_id': field.id, 'show_if_field_values': ['yes']})
        assert exc_info.value.messages == {
            'show_if_field_id': ['The field cannot conditionally depend on itself to be shown']
        }

    def test_show_if_field_from_other_regform(self, db, dummy_regform, dummy_event, create_regform):
        other_regform = create_regform(dummy_event, title='Other Form')
        other_section = RegistrationFormSection(registration_form=other_regform, title='Other section',
                                                is_manager_only=False)
        other_condition_field = RegistrationFormField(parent=other_section, registration_form=other_regform)
        _fill_form_field_with_data(other_condition_field, {'input_type': 'checkbox', 'title': 'Condition field'})
        db.session.flush()
        section = RegistrationFormSection(registration_form=dummy_regform, title='Section', is_manager_only=False)
        new_field = RegistrationFormField(parent=section, registration_form=dummy_regform)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_field})
        with pytest.raises(ValidationError) as exc_info:
            schema.load({'input_type': 'text', 'title': 'New field',
                         'show_if_field_id': other_condition_field.id, 'show_if_field_values': ['yes']})
        assert exc_info.value.messages == {
            'show_if_field_id': ['The field to show does not belong to the same registration form.']
        }

    def test_show_if_field_unsupported_input_type(self, db, dummy_regform):
        section = RegistrationFormSection(registration_form=dummy_regform, title='Section', is_manager_only=False)
        condition_field = RegistrationFormField(parent=section, registration_form=dummy_regform)
        _fill_form_field_with_data(condition_field, {'input_type': 'text', 'title': 'Condition field'})
        db.session.flush()
        new_field = RegistrationFormField(parent=section, registration_form=dummy_regform)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_field})
        with pytest.raises(ValidationError) as exc_info:
            schema.load({'input_type': 'text', 'title': 'New field',
                         'show_if_field_id': condition_field.id, 'show_if_field_values': ['yes']})
        assert exc_info.value.messages == {'show_if_field_id': ['This field cannot be used as a condition.']}

    def test_show_if_field_cycle_detection(self, db, dummy_regform):
        section = RegistrationFormSection(registration_form=dummy_regform, title='Section', is_manager_only=False)
        field_a = RegistrationFormField(parent=section, registration_form=dummy_regform)
        _fill_form_field_with_data(field_a, {'input_type': 'checkbox', 'title': 'Field A'})
        db.session.flush()
        field_b = RegistrationFormField(parent=section, registration_form=dummy_regform)
        _fill_form_field_with_data(field_b, {'input_type': 'checkbox', 'title': 'Field B'})
        field_b.show_if_id = field_a.id
        field_b.show_if_values = ['yes']
        db.session.flush()
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': field_a})
        with pytest.raises(ValidationError) as exc_info:
            schema.load({'input_type': 'checkbox', 'title': 'Field A',
                         'show_if_field_id': field_b.id, 'show_if_field_values': ['yes']})
        assert exc_info.value.messages == {
            'show_if_field_id': ['Field conditions may not have cycles (a -> b -> c -> a)']
        }

    def test_show_if_field_condition_in_manager_only_section(self, db, dummy_regform):
        manager_section = RegistrationFormSection(registration_form=dummy_regform, title='Manager section',
                                                  is_manager_only=True)
        condition_field = RegistrationFormField(parent=manager_section, registration_form=dummy_regform)
        _fill_form_field_with_data(condition_field, {'input_type': 'checkbox', 'title': 'Manager condition'})
        db.session.flush()
        new_section = RegistrationFormSection(registration_form=dummy_regform, title='Section', is_manager_only=False)
        new_field = RegistrationFormField(parent=new_section, registration_form=dummy_regform)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_field})
        with pytest.raises(ValidationError) as exc_info:
            schema.load({'input_type': 'text', 'title': 'New field',
                         'show_if_field_id': condition_field.id, 'show_if_field_values': ['yes']})
        assert exc_info.value.messages == {
            'show_if_field_id': ['Field conditions may not depend on fields in manager-only sections']
        }

    def test_show_if_field_does_not_allow_disabled_field(self, db, dummy_regform):
        new_section = RegistrationFormSection(registration_form=dummy_regform, title='New section',
                                              is_manager_only=False)
        condition_field = RegistrationFormField(parent=new_section, registration_form=dummy_regform)
        _fill_form_field_with_data(condition_field, {'input_type': 'checkbox', 'title': 'Condition field'})
        condition_field.is_enabled = False
        db.session.flush()
        new_field = RegistrationFormField(parent=new_section, registration_form=dummy_regform)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_field})
        with pytest.raises(ValidationError) as exc_info:
            schema.load({'input_type': 'text', 'title': 'New field',
                         'show_if_field_id': condition_field.id, 'show_if_field_values': ['yes']})
        assert exc_info.value.messages == {'show_if_field_id': ['Disabled fields cannot be used as a condition.']}

    def test_show_if_field_allows_existing_disabled_field(self, db, dummy_regform):
        condition_section = RegistrationFormSection(registration_form=dummy_regform, title='Condition section',
                                                    is_manager_only=False)
        condition_field = RegistrationFormField(parent=condition_section, registration_form=dummy_regform)
        _fill_form_field_with_data(condition_field, {'input_type': 'checkbox', 'title': 'Condition field'})
        new_section = RegistrationFormSection(registration_form=dummy_regform, title='New section',
                                                    is_manager_only=False)
        new_field = RegistrationFormField(parent=new_section, registration_form=dummy_regform)
        _fill_form_field_with_data(new_field, {'input_type': 'text', 'title': 'New field'})
        db.session.flush()
        new_field.show_if_id = condition_field.id
        new_field.show_if_values = ['yes']
        db.session.flush()
        condition_field.is_enabled = False
        db.session.flush()
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_field})
        assert schema.load({'input_type': 'text', 'title': 'New field',
                            'show_if_field_id': condition_field.id, 'show_if_field_values': ['yes']})

    def test_show_if_field_does_not_allow_fields_in_disabled_section(self, db, dummy_regform):
        section = RegistrationFormSection(registration_form=dummy_regform, title='Condition section',
                                          is_manager_only=False)
        condition_field = RegistrationFormField(parent=section, registration_form=dummy_regform)
        _fill_form_field_with_data(condition_field, {'input_type': 'checkbox', 'title': 'Condition field'})
        section.is_enabled = False
        db.session.flush()
        new_section = RegistrationFormSection(registration_form=dummy_regform, title='New section',
                                                is_manager_only=False)
        new_field = RegistrationFormField(parent=new_section, registration_form=dummy_regform)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_field})
        with pytest.raises(ValidationError) as exc_info:
            schema.load({'input_type': 'text', 'title': 'New field',
                         'show_if_field_id': condition_field.id, 'show_if_field_values': ['yes']})
        assert exc_info.value.messages == {
            'show_if_field_id': ['Fields in disabled sections cannot be used as a condition.']
        }


class TestRegistrationFormToggleFieldState:
    # title tests

    def test_unique_title_on_enable(self, db, dummy_regform):
        pd_section = dummy_regform.sections[0]
        disabled_field = RegistrationFormField(parent=pd_section, registration_form=dummy_regform, is_enabled=False)
        _fill_form_field_with_data(disabled_field, {'input_type': 'text', 'title': 'Unique Title'})
        db.session.flush()
        rh = RHRegistrationFormToggleFieldState()
        rh.field = disabled_field
        assert rh._check_unique_title_in_section() is None

    def test_same_title_on_enable(self, db, dummy_regform):
        pd_section = dummy_regform.sections[0]
        disabled_field = RegistrationFormField(parent=pd_section, registration_form=dummy_regform, is_enabled=False,
                                               id=1337)
        _fill_form_field_with_data(disabled_field, {'input_type': 'text', 'title': 'Title'})
        db.session.flush()
        rh = RHRegistrationFormToggleFieldState()
        rh.field = disabled_field
        with pytest.raises(BadRequest, match='There is already a field in this section with the same title'):
            rh._check_unique_title_in_section()

    def test_same_title_in_other_section_on_enable(self, db, dummy_regform):
        other_section = RegistrationFormSection(registration_form=dummy_regform, title='Other Section',
                                                is_manager_only=False)
        disabled_field = RegistrationFormField(parent=other_section, registration_form=dummy_regform, is_enabled=False,
                                               id=1337)
        _fill_form_field_with_data(disabled_field, {'input_type': 'text', 'title': 'Title'})
        db.session.flush()
        rh = RHRegistrationFormToggleFieldState()
        rh.field = disabled_field
        assert rh._check_unique_title_in_section() is None

    # internal_name tests

    def test_empty_internal_name_on_enable(self, db, dummy_regform):
        pd_section = dummy_regform.sections[0]
        disabled_field = RegistrationFormField(parent=pd_section, registration_form=dummy_regform, is_enabled=False)
        _fill_form_field_with_data(disabled_field, {'input_type': 'text', 'title': 'Field Title'})
        db.session.flush()
        rh = RHRegistrationFormToggleFieldState()
        rh.field = disabled_field
        assert rh._check_unique_internal_name_in_form() is None

    def test_multiple_fields_with_empty_internal_name_on_enable(self, db, dummy_regform):
        pd_section = dummy_regform.sections[0]
        enabled_field = RegistrationFormField(parent=pd_section, registration_form=dummy_regform)
        _fill_form_field_with_data(enabled_field, {'input_type': 'text', 'title': 'Enabled Field Title'})
        disabled_field = RegistrationFormField(parent=pd_section, registration_form=dummy_regform, is_enabled=False)
        _fill_form_field_with_data(disabled_field, {'input_type': 'text', 'title': 'Disabled Field Title'})
        db.session.flush()
        rh = RHRegistrationFormToggleFieldState()
        rh.field = disabled_field
        assert rh._check_unique_internal_name_in_form() is None

    def test_unique_internal_name_on_enable(self, db, dummy_regform):
        pd_section = dummy_regform.sections[0]
        disabled_field = RegistrationFormField(parent=pd_section, registration_form=dummy_regform, is_enabled=False)
        _fill_form_field_with_data(disabled_field, {'input_type': 'text', 'title': 'Field Title',
                                                    'internal_name': 'unique-internal-name'})
        db.session.flush()
        rh = RHRegistrationFormToggleFieldState()
        rh.field = disabled_field
        assert rh._check_unique_internal_name_in_form() is None

    def test_same_internal_name_on_enable(self, db, dummy_regform):
        pd_section = dummy_regform.sections[0]
        disabled_field = RegistrationFormField(parent=pd_section, registration_form=dummy_regform, is_enabled=False)
        _fill_form_field_with_data(disabled_field, {'input_type': 'text', 'title': 'Field Title',
                                                    'internal_name': 'title'})
        db.session.flush()
        rh = RHRegistrationFormToggleFieldState()
        rh.field = disabled_field
        with pytest.raises(BadRequest, match='The field "Title" on this form has the same internal name'):
            rh._check_unique_internal_name_in_form()

    def test_same_internal_name_in_other_section_on_enable(self, db, dummy_regform):
        other_section = RegistrationFormSection(registration_form=dummy_regform, title='Other Section',
                                                is_manager_only=False)
        disabled_field = RegistrationFormField(parent=other_section, registration_form=dummy_regform, is_enabled=False,
                                               id=1337)
        _fill_form_field_with_data(disabled_field, {'input_type': 'text', 'title': 'Field Title',
                                                    'internal_name': 'title'})
        db.session.flush()
        rh = RHRegistrationFormToggleFieldState()
        rh.field = disabled_field
        with pytest.raises(BadRequest, match='The field "Title" on this form has the same internal name'):
            rh._check_unique_internal_name_in_form()

    def test_consistent_type_on_enabled(self, db, dummy_regform, create_regform):
        other_regform = create_regform(dummy_regform.event, title='Other Form')
        other_pd_section = other_regform.sections[0]
        other_field = RegistrationFormField(parent=other_pd_section, registration_form=other_regform)
        _fill_form_field_with_data(other_field, {'input_type': 'text', 'title': 'Field Title',
                                                 'internal_name': 'unique-internal-name'})
        db.session.flush()

        pd_section = dummy_regform.sections[0]
        disabled_field = RegistrationFormField(parent=pd_section, registration_form=dummy_regform, is_enabled=False)
        _fill_form_field_with_data(disabled_field, {'input_type': 'text', 'title': 'Field Title',
                                                    'internal_name': 'unique-internal-name'})
        db.session.flush()
        rh = RHRegistrationFormToggleFieldState()
        rh.field = disabled_field
        assert rh._check_internal_name_type_consistency_in_event() is None

    def test_inconsistent_type_on_enabled(self, db, dummy_regform, create_regform):
        other_regform = create_regform(dummy_regform.event, title='Other Form')
        other_pd_section = other_regform.sections[0]
        other_field = RegistrationFormField(parent=other_pd_section, registration_form=other_regform)
        _fill_form_field_with_data(other_field, {'input_type': 'text', 'title': 'Field Title',
                                                 'internal_name': 'unique-internal-name'})
        db.session.flush()

        pd_section = dummy_regform.sections[0]
        disabled_field = RegistrationFormField(parent=pd_section, registration_form=dummy_regform, is_enabled=False)
        _fill_form_field_with_data(disabled_field, {'input_type': 'textarea', 'title': 'Field Title',
                                                    'internal_name': 'unique-internal-name'})
        db.session.flush()
        rh = RHRegistrationFormToggleFieldState()
        rh.field = disabled_field
        with pytest.raises(BadRequest, match='The field "Field Title" with the same internal name on form "Other Form" '
                                             'uses a different input type which is not allowed'):
            rh._check_internal_name_type_consistency_in_event()


class TestRegistrationFormModifyField:
    def test_delete_condition_field_clears_show_if_field_and_values(self, db, dummy_regform, app_context):
        section = RegistrationFormSection(registration_form=dummy_regform, title='Section', is_manager_only=False)
        condition_field = RegistrationFormField(parent=section, registration_form=dummy_regform)
        _fill_form_field_with_data(condition_field, {'input_type': 'checkbox', 'title': 'Condition field'})
        db.session.flush()
        new_field = RegistrationFormField(parent=section, registration_form=dummy_regform)
        _fill_form_field_with_data(new_field, {'input_type': 'text', 'title': 'New field'})
        new_field.show_if_id = condition_field.id
        new_field.show_if_values = ['yes']
        db.session.flush()
        with app_context.test_request_context():
            rh = RHRegistrationFormModifyField()
            rh.field = condition_field
            rh.regform = dummy_regform
            rh._process_DELETE()
        assert new_field.show_if_id is None
        assert new_field.show_if_values is None

    def test_delete_field_clears_condition_for_links(self, db, dummy_regform, app_context):
        section = RegistrationFormSection(registration_form=dummy_regform, title='Section', is_manager_only=False)
        condition_field = RegistrationFormField(parent=section, registration_form=dummy_regform)
        _fill_form_field_with_data(condition_field, {'input_type': 'checkbox', 'title': 'Condition field'})
        db.session.flush()
        new_field = RegistrationFormField(parent=section, registration_form=dummy_regform)
        _fill_form_field_with_data(new_field, {'input_type': 'text', 'title': 'New field'})
        new_field.show_if_id = condition_field.id
        new_field.show_if_values = ['yes']
        db.session.flush()
        with app_context.test_request_context():
            rh = RHRegistrationFormModifyField()
            rh.field = new_field
            rh.regform = dummy_regform
            rh._process_DELETE()
        assert condition_field.condition_for == []
