# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from flask import current_app
from wtforms import ValidationError

from indico.modules.events.registration.models.form_fields import (RegistrationFormPersonalDataField,
                                                                   RegistrationFormFieldData)
from indico.modules.events.registration.models.items import (RegistrationFormPersonalDataSection,
                                                             RegistrationFormItemType, PersonalDataType)
from indico.web.forms.base import IndicoForm


def get_event_section_data(regform, management=False):
    return [s.view_data for s in regform.sections if not s.is_deleted and (management or not s.is_manager_only)]


def make_registration_form(regform, management=False):
    """Creates a WTForm based on registration form fields"""

    class RegistrationFormWTF(IndicoForm):
        def validate_email(self, field):
            if regform.get_registration(email=field.data):
                raise ValidationError('Email already in use')

    for form_item in regform.active_fields:
        if not management and form_item.parent.is_manager_only:
            continue
        field_impl = form_item.field_impl
        setattr(RegistrationFormWTF, form_item.html_field_name, field_impl.create_wtf_field())
    return RegistrationFormWTF


def create_personal_data_fields(regform):
    """Creates the special section/fields for personal data."""
    section = next((s for s in regform.sections if s.type == RegistrationFormItemType.section_pd), None)
    if section is None:
        section = RegistrationFormPersonalDataSection(registration_form=regform, title='Personal Data')
        missing = set(PersonalDataType)
    else:
        existing = {x.personal_data_type for x in section.children if x.type == RegistrationFormItemType.field_pd}
        missing = set(PersonalDataType) - existing
    for pd_type, data in PersonalDataType.FIELD_DATA:
        if pd_type not in missing:
            continue
        field = RegistrationFormPersonalDataField(registration_form=regform, personal_data_type=pd_type,
                                                  is_required=pd_type.is_required)
        field.data = data.pop('data', {})
        field.current_data = RegistrationFormFieldData(field=field, versioned_data=data.pop('versioned_data', {}))
        for key, value in data.iteritems():
            setattr(field, key, value)
        section.children.append(field)


def url_rule_to_angular(endpoint):
    """Converts a flask-style rule to angular style"""
    mapping = {
        'reg_form_id': 'confFormId',
        'section_id': 'sectionId',
        'field_id': 'fieldId',
    }
    rules = list(current_app.url_map.iter_rules(endpoint))
    assert len(rules) == 1
    rule = rules[0]
    assert not rule.defaults
    segments = [':' + mapping.get(data, data) if is_dynamic else data
                for is_dynamic, data in rule._trace]
    return ''.join(segments).split('|', 1)[-1]
