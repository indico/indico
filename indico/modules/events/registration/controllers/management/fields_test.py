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
from indico.modules.events.registration.models.registrations import RegistrationState


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


class TestGeneralFieldDataSchema:
    def test_add_new_field_with_same_title_in_same_section(self, dummy_regform):
        pd_section = dummy_regform.sections[0]
        first_name_field = next(
            (field for field in pd_section.fields if field.personal_data_type == PersonalDataType.first_name), None
        )
        new_field = RegistrationFormField(parent=pd_section, registration_form=dummy_regform)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_field})
        with pytest.raises(ValidationError) as exc_info:
            schema.load({'input_type': 'text', 'title': first_name_field.title})
        assert exc_info.value.messages == {'title': 'There is already a field in this section with the same title.'}

    def test_modify_field_with_same_title_in_same_section(self, dummy_regform):
        pd_section = dummy_regform.sections[0]
        first_name_field = next(
            (field for field in pd_section.fields if field.personal_data_type == PersonalDataType.first_name), None
        )
        last_name_field = next(
            (field for field in pd_section.fields if field.personal_data_type == PersonalDataType.last_name), None
        )
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': last_name_field})
        with pytest.raises(ValidationError) as exc_info:
            schema.load({'input_type': last_name_field.input_type, 'title': first_name_field.title})
        assert exc_info.value.messages == {'title': 'There is already a field in this section with the same title.'}

    def test_update_title_of_disabled_field(self, dummy_regform):
        pd_section = dummy_regform.sections[0]
        position_field = next(
            (field for field in pd_section.fields if field.personal_data_type == PersonalDataType.position), None
        )
        disabled_field = RegistrationFormField(
            parent=pd_section, registration_form=dummy_regform, is_enabled=False, id=1337
        )
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': disabled_field})
        assert schema.load({'input_type': 'text', 'title': position_field.title})

    def test_add_new_field_with_same_title_but_disabled(self, db, dummy_regform):
        pd_section = dummy_regform.sections[0]
        affiliation_field = next(
            (field for field in pd_section.fields if field.personal_data_type == PersonalDataType.affiliation), None
        )
        affiliation_field.is_enabled = False
        db.session.flush()
        new_affiliation_field = RegistrationFormField(parent=pd_section, registration_form=dummy_regform)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_affiliation_field})
        assert schema.load({'input_type': 'text', 'title': affiliation_field.title})

    def test_add_new_field_with_same_title_in_other_section(self, dummy_regform):
        pd_section = dummy_regform.sections[0]
        first_name_field = next(
            (field for field in pd_section.fields if field.personal_data_type == PersonalDataType.first_name), None
        )
        new_section = RegistrationFormSection(
            registration_form=dummy_regform, title='New Section', is_manager_only=False
        )
        new_field = RegistrationFormField(parent=new_section, registration_form=dummy_regform)
        schema = GeneralFieldDataSchema(context={'regform': dummy_regform, 'field': new_field})
        assert schema.load({'input_type': 'text', 'title': first_name_field.title})


class TestAccompanyingPersonsFieldSetupSchema:
    @staticmethod
    def _set_registration_inactive(registration, **changes):
        for key, value in changes.items():
            setattr(registration, key, value)

    @staticmethod
    def _load_schema(field, **kwargs):
        schema = field.field_impl.create_setup_schema(context={'regform': field.registration_form, 'field': field})
        return schema.load(
            {
                'price': 0,
                'max_persons': 0,
                'persons_count_against_limit': False,
                'is_anonymous': False,
            }
            | kwargs
        )

    def test_reject_enabling_anonymous_mode_when_accompanying_person_tickets_enabled(
        self, dummy_regform, create_accompanying_persons_field
    ):
        dummy_regform.tickets_for_accompanying_persons = True
        field = create_accompanying_persons_field(0, False)

        with pytest.raises(ValidationError) as exc_info:
            self._load_schema(field, is_anonymous=True)

        assert exc_info.value.messages == {
            'is_anonymous': 'Anonymous accompanying persons cannot be enabled while tickets for accompanying '
            'persons are enabled.'
        }

    @pytest.mark.usefixtures('dummy_reg')
    def test_reject_enabling_anonymous_mode_when_named_accompanying_person_registrations_exist(
        self, dummy_reg, create_accompanying_persons_field
    ):
        field = create_accompanying_persons_field(0, False, registration=dummy_reg, num_persons=1)

        with pytest.raises(ValidationError) as exc_info:
            self._load_schema(field, is_anonymous=True)

        assert exc_info.value.messages == {
            'is_anonymous': 'Cannot be enabled when accompanying persons are registered.'
        }

    @pytest.mark.parametrize(
        'changes',
        ({'is_deleted': True}, {'state': RegistrationState.withdrawn}, {'state': RegistrationState.rejected}),
        ids=('deleted', 'withdrawn', 'rejected'),
    )
    @pytest.mark.usefixtures('dummy_reg')
    def test_allow_enabling_anonymous_mode_when_only_inactive_registrations_exist(
        self, db, dummy_reg, create_accompanying_persons_field, changes
    ):
        field = create_accompanying_persons_field(0, False, registration=dummy_reg, num_persons=1)
        self._set_registration_inactive(dummy_reg, **changes)
        db.session.flush()

        data = self._load_schema(field, is_anonymous=True)

        assert data['is_anonymous'] is True
        assert not field.field_impl.is_anonymous_locked
        assert field.field_impl.anonymous_lock_reason is None

    def test_allow_disabling_anonymous_mode_without_accompanying_person_registrations(
        self, create_accompanying_persons_field
    ):
        field = create_accompanying_persons_field(0, False, is_anonymous=True)

        data = self._load_schema(field, is_anonymous=False)

        assert data['is_anonymous'] is False
        assert not field.field_impl.is_anonymous_locked
        assert field.field_impl.anonymous_lock_reason is None

    @pytest.mark.parametrize(
        'changes',
        ({'is_deleted': True}, {'state': RegistrationState.withdrawn}, {'state': RegistrationState.rejected}),
        ids=('deleted', 'withdrawn', 'rejected'),
    )
    @pytest.mark.usefixtures('dummy_reg')
    def test_allow_disabling_anonymous_mode_when_only_inactive_registrations_exist(
        self, db, dummy_reg, create_accompanying_persons_field, changes
    ):
        field = create_accompanying_persons_field(0, False, registration=dummy_reg, data=1, is_anonymous=True)
        self._set_registration_inactive(dummy_reg, **changes)
        db.session.flush()

        data = self._load_schema(field, is_anonymous=False)

        assert data['is_anonymous'] is False
        assert not field.field_impl.is_anonymous_locked
        assert field.field_impl.anonymous_lock_reason is None

    @pytest.mark.usefixtures('dummy_reg')
    def test_reject_disabling_anonymous_mode_when_anonymous_accompanying_person_registrations_exist(
        self, dummy_reg, create_accompanying_persons_field
    ):
        field = create_accompanying_persons_field(0, False, registration=dummy_reg, data=1, is_anonymous=True)

        with pytest.raises(ValidationError) as exc_info:
            self._load_schema(field, is_anonymous=False)

        assert exc_info.value.messages == {
            'is_anonymous': 'Cannot be switched back to named mode when anonymous accompanying persons are registered.'
        }
