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

from indico.core.db import db
from indico.modules.events.registration import logger
from indico.modules.events.registration.controllers.management.sections import RHManageRegFormSectionBase
from indico.modules.events.registration.models.items import (RegistrationFormText, RegistrationFormItem,
                                                             RegistrationFormItemType)
from indico.modules.events.registration.models.form_fields import (RegistrationFormField, RegistrationFormFieldData)
from indico.util.string import snakify_keys
from indico.web.util import jsonify_data
from uuid import uuid4

NON_VERSIONED_DATA = {'min_value', 'length', 'number_of_columns', 'number_of_rows', 'places_limit', 'date_format',
                      'with_extra_slots', 'item_type', 'default_item', 'time_format'}


def _fill_form_field_with_data(field, field_data):
    field.title = field_data.pop('title')
    field.description = field_data.pop('description', '')
    field.is_enabled = field_data.pop('is_enabled')
    field.is_required = field_data.pop('is_required', False)
    field.input_type = field_data.pop('input_type', None)
    field.data = {key: field_data.pop(key) for key in NON_VERSIONED_DATA if key in field_data}


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
        self.field.is_enabled = (request.args.get('enable') == 'true')
        db.session.flush()
        logger.info('Field {} modified by {}'.format(self.field, session.user))
        return jsonify_data(**self.field.view_data)


class RHRegistrationFormModifyField(RHManageRegFormFieldBase):
    """Remove/Modify a field"""

    def _process_DELETE(self):
        self.field.is_deleted = True
        db.session.flush()
        logger.info('Field {} deleted by {}'.format(self.field, session.user))
        return jsonify_data(flash=False)

    def _process_POST(self):
        field_data = snakify_keys(request.json['fieldData'])
        if self.field.type == RegistrationFormItemType.text:
            del field_data['input_type']  # labels have no input type
        _fill_form_field_with_data(self.field, field_data)
        if field_data != self.field.current_data.versioned_data:
            if self.field.input_type == 'radio':
                for item in field_data['radioitems']:
                    if not item.get('id', None):
                        item['id'] = unicode(uuid4())
            self.field.current_data = RegistrationFormFieldData(field_id=self.field.id, versioned_data=field_data)
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
        if field_data['input_type'] == 'date':
            date_format = field_data['date_format'].split(' ')
            field_data['date_format'] = date_format[0]
            if len(date_format) == 2:
                field_data['time_format'] = date_format[1]
        elif field_data['input_type'] == 'radio':
            items = field_data['radioitems']
            for item in items:
                item['id'] = unicode(uuid4())

        if field_data['input_type'] == 'label':
            del field_data['input_type']  # labels have no input type
            field_type = RegistrationFormText
        else:
            field_type = RegistrationFormField
        form_field = field_type(parent_id=self.section.id, registration_form=self.regform)
        _fill_form_field_with_data(form_field, field_data)
        db.session.add(form_field)
        db.session.flush()
        form_field.current_data = RegistrationFormFieldData(field_id=form_field.id, versioned_data=field_data)
        return jsonify(form_field.view_data)
