# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from flask import jsonify, request, session
from werkzeug.exceptions import BadRequest

from indico.core.db import db
from indico.modules.events.registration import logger
from indico.modules.events.registration.controllers.management.sections import RHManageRegFormSectionBase
from indico.modules.events.registration.models.form_fields import RegistrationFormField
from indico.modules.events.registration.models.items import RegistrationFormItemType, RegistrationFormText
from indico.modules.events.registration.util import update_regform_item_positions
from indico.util.string import snakify_keys


def _fill_form_field_with_data(field, field_data, set_data=True):
    field.title = field_data.pop('title')
    field.description = field_data.pop('description', '')
    field.is_enabled = field_data.pop('is_enabled')
    field.is_required = field_data.pop('is_required', False)
    field.input_type = field_data.pop('input_type', None)
    if set_data:
        if field.id is None:  # new field
            field.data, field.versioned_data = field.field_impl.process_field_data(field_data)
        else:
            field.data, field.versioned_data = field.field_impl.process_field_data(field_data, field.data,
                                                                                   field.versioned_data)


class RHManageRegFormFieldBase(RHManageRegFormSectionBase):
    """Base class for a specific field within a registration form"""

    field_class = RegistrationFormField
    normalize_url_spec = {
        'locators': {
            lambda self: self.field
        }
    }

    def _process_args(self):
        RHManageRegFormSectionBase._process_args(self)
        self.field = self.field_class.get_one(request.view_args['field_id'])


class RHRegistrationFormToggleFieldState(RHManageRegFormFieldBase):
    """Enable/Disable a field"""

    def _process(self):
        enabled = request.args.get('enable') == 'true'
        if (not enabled and self.field.type == RegistrationFormItemType.field_pd and
                self.field.personal_data_type.is_required):
            raise BadRequest
        self.field.is_enabled = enabled
        update_regform_item_positions(self.regform)
        db.session.flush()
        logger.info('Field %s modified by %s', self.field, session.user)
        return jsonify(view_data=self.field.view_data)


class RHRegistrationFormModifyField(RHManageRegFormFieldBase):
    """Remove/Modify a field"""

    def _process_DELETE(self):
        if self.field.type == RegistrationFormItemType.field_pd:
            raise BadRequest
        self.field.is_deleted = True
        update_regform_item_positions(self.regform)
        db.session.flush()
        logger.info('Field %s deleted by %s', self.field, session.user)
        return jsonify()

    def _process_PATCH(self):
        field_data = snakify_keys(request.json['fieldData'])
        if (self.field.type == RegistrationFormItemType.field_pd and self.field.personal_data_type.is_required and
                not field_data['is_required']):
            raise BadRequest
        elif self.field.input_type != field_data['input_type']:
            raise BadRequest
        _fill_form_field_with_data(self.field, field_data)
        return jsonify(view_data=self.field.view_data)


class RHRegistrationFormMoveField(RHManageRegFormFieldBase):
    """Change position of a field within the section"""

    def _process(self):
        new_position = request.json['endPos'] + 1
        old_position = self.field.position
        if new_position == old_position:
            return jsonify()
        elif new_position < old_position:
            def fn(field):
                return (field.position >= new_position and field.id != self.field.id and not field.is_deleted and
                        field.is_enabled)
            start_enum = new_position + 1
        else:
            def fn(field):
                return (old_position < field.position <= new_position and field.id != self.field.id and
                        not field.is_deleted and field.is_enabled)
            start_enum = self.field.position
        to_update = filter(fn, self.section.children)
        self.field.position = new_position
        for pos, field in enumerate(to_update, start_enum):
            field.position = pos
        db.session.flush()
        return jsonify()


class RHRegistrationFormAddField(RHManageRegFormSectionBase):
    """Add a field to the section"""

    def _process(self):
        field_data = snakify_keys(request.json['fieldData'])
        form_field = RegistrationFormField(parent_id=self.section.id, registration_form=self.regform)
        _fill_form_field_with_data(form_field, field_data)
        db.session.add(form_field)
        db.session.flush()
        return jsonify(view_data=form_field.view_data)


class RHRegistrationFormToggleTextState(RHRegistrationFormToggleFieldState):
    """Enable/Disable a static text field"""
    field_class = RegistrationFormText


class RHRegistrationFormModifyText(RHRegistrationFormModifyField):
    """Remove/Modify a static text field"""
    field_class = RegistrationFormText

    def _process_PATCH(self):
        field_data = snakify_keys(request.json['fieldData'])
        del field_data['input_type']
        _fill_form_field_with_data(self.field, field_data, set_data=False)
        return jsonify(view_data=self.field.view_data)


class RHRegistrationFormMoveText(RHRegistrationFormMoveField):
    """Change position of a static text field within the section"""
    field_class = RegistrationFormText


class RHRegistrationFormAddText(RHManageRegFormSectionBase):
    """Add a static text field to a section"""

    def _process(self):
        field_data = snakify_keys(request.json['fieldData'])
        del field_data['input_type']
        form_field = RegistrationFormText(parent_id=self.section.id, registration_form=self.regform)
        _fill_form_field_with_data(form_field, field_data, set_data=False)
        db.session.add(form_field)
        db.session.flush()
        return jsonify(view_data=form_field.view_data)
