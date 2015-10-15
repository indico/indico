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

from flask import request, jsonify, session
from werkzeug.exceptions import BadRequest

from indico.core.db import db
from indico.modules.events.registration import logger
from indico.modules.events.registration.controllers.management.sections import RHManageRegFormSectionBase
from indico.modules.events.registration.fields import get_field_types
from indico.modules.events.registration.models.items import (RegistrationFormText, RegistrationFormItem,
                                                             RegistrationFormItemType)
from indico.modules.events.registration.models.form_fields import (RegistrationFormField, RegistrationFormFieldData)
from indico.util.string import snakify_keys
from indico.web.util import jsonify_data


def _fill_form_field_with_data(field, field_data):
    field.title = field_data.pop('title')
    field.description = field_data.pop('description', '')
    field.is_enabled = field_data.pop('is_enabled')
    field.is_required = field_data.pop('is_required', False)
    field.input_type = field_data.pop('input_type', None)


class RHManageRegFormFieldBase(RHManageRegFormSectionBase):
    """Base class for a specific field within a registration form"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.field
        }
    }

    def _checkParams(self, params):
        RHManageRegFormSectionBase._checkParams(self, params)
        self.field = RegistrationFormItem.get_one(request.view_args['field_id'])


class RHRegistrationFormToggleFieldState(RHManageRegFormFieldBase):
    """Enable/Disable a field"""

    def _process(self):
        enabled = request.args.get('enable') == 'true'
        if (not enabled and self.field.type == RegistrationFormItemType.field_pd and
                self.field.personal_data_type.is_required):
            raise BadRequest
        self.field.is_enabled = enabled
        db.session.flush()
        logger.info('Field {} modified by {}'.format(self.field, session.user))
        return jsonify_data(**self.field.view_data)


class RHRegistrationFormModifyField(RHManageRegFormFieldBase):
    """Remove/Modify a field"""

    def _process_DELETE(self):
        if self.field.type == RegistrationFormItemType.field_pd:
            raise BadRequest
        self.field.is_deleted = True
        db.session.flush()
        logger.info('Field {} deleted by {}'.format(self.field, session.user))
        return jsonify_data(flash=False)

    def _process_PATCH(self):
        field_data = snakify_keys(request.json['fieldData'])
        if (self.field.type == RegistrationFormItemType.field_pd and self.field.personal_data_type.is_required and
                not field_data['is_required']):
            raise BadRequest
        if self.field.type == RegistrationFormItemType.text:
            del field_data['input_type']  # labels have no input type
        elif self.field.input_type != field_data['input_type']:
            raise BadRequest
        _fill_form_field_with_data(self.field, field_data)
        if self.field.type != RegistrationFormItemType.text:
            self.field.data, self.field.versioned_data = self.field.field_impl.process_field_data(
                field_data, self.field.data, self.field.versioned_data)
        return jsonify_data(flash=False)


class RHRegistrationFormMoveField(RHManageRegFormFieldBase):
    """Change position of a field within the section"""

    def _process(self):
        new_position = request.json['endPos'] + 1
        old_position = self.field.position
        if new_position == old_position:
            return jsonify(success=True)
        elif new_position < old_position:
            def fn(field):
                return field.position >= new_position and field.id != self.field.id and not field.is_deleted
            start_enum = new_position + 1
        else:
            def fn(field):
                return (field.position > old_position and field.position <= new_position
                        and field.id != self.field.id and not field.is_deleted)
            start_enum = self.field.position
        to_update = filter(fn, self.section.children)
        self.field.position = new_position
        for pos, field in enumerate(to_update, start_enum):
            field.position = pos
        db.session.flush()
        return jsonify(success=True)


class RHRegistrationFormAddField(RHManageRegFormSectionBase):
    """Add a field to the section"""

    def _process(self):
        field_data = snakify_keys(request.json['fieldData'])
        if field_data['input_type'] == 'label':
            del field_data['input_type']  # labels have no input type
            field_type = RegistrationFormText
            data = versioned_data = None
        else:
            field_type = RegistrationFormField
            try:
                field_impl_type = get_field_types()[field_data['input_type']]
            except KeyError:
                raise BadRequest
            data, versioned_data = field_impl_type.process_field_data(field_data)

        form_field = field_type(parent_id=self.section.id, registration_form=self.regform)
        _fill_form_field_with_data(form_field, field_data)
        if data is not None:
            form_field.data = data
        if versioned_data is not None:
            form_field.versioned_data = versioned_data
        db.session.add(form_field)
        db.session.flush()
        return jsonify(form_field.view_data)
