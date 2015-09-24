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
from indico.modules.events.registration.models.items import RegistrationFormText, RegistrationFormItem
from indico.modules.events.registration.models.registration_form_fields import (RegistrationFormField,
                                                                                RegistrationFormFieldData)
from indico.web.util import jsonify_data

NON_VERSIONED_DATA = {'minValue', 'length', 'numberOfColumns', 'numberOfRows', 'placesLimit', 'dateFormat',
                      'withExtraSlots', 'inputType', 'defaultItem', 'timeFormat'}


def _fill_form_field_with_data(field, field_data):
    field.title = field_data.pop('caption')
    field.description = field_data.pop('description', '')
    field.is_enabled = not field_data.pop('disabled')
    field.is_required = field_data.pop('mandatory', False)
    field.input_type = field_data.pop('input')
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
        return jsonify_data(success=True)

    def _process_POST(self):
        field_data = request.json['fieldData']
        _fill_form_field_with_data(self.field, field_data)
        if field_data != self.field.current_data.versioned_data:
            self.field.current_data = RegistrationFormFieldData(field_id=self.field.id, versioned_data=field_data)
        return jsonify(self.field.view_data)


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
        field_data = request.json['fieldData']
        if field_data['input'] == 'date':
            dateFormat = field_data['dateFormat'].split(' ')
            field_data['dateFormat'] = dateFormat[0]
            if len(dateFormat) == 2:
                field_data['timeFormat'] = dateFormat[1]

        if field_data['input'] == 'label':
            field_type = RegistrationFormText
        else:
            field_type = RegistrationFormField
        form_field = field_type(parent_id=self.section.id, registration_form=self.regform)
        _fill_form_field_with_data(form_field, field_data)
        db.session.add(form_field)
        db.session.flush()
        form_field.current_data = RegistrationFormFieldData(field_id=form_field.id, versioned_data=field_data)
        return jsonify(form_field.view_data)
