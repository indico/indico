# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import jsonify, request, session
from marshmallow import EXCLUDE, ValidationError, fields, post_load, pre_load, validates
from werkzeug.exceptions import BadRequest

from indico.core.db import db
from indico.core.marshmallow import mm
from indico.modules.events.registration import logger
from indico.modules.events.registration.controllers.management.sections import RHManageRegFormSectionBase
from indico.modules.events.registration.fields import get_field_types
from indico.modules.events.registration.models.form_fields import RegistrationFormField
from indico.modules.events.registration.models.items import RegistrationFormItemType, RegistrationFormText
from indico.modules.events.registration.util import update_regform_item_positions
from indico.util.marshmallow import not_empty
from indico.util.string import snakify_keys


class GeneralFieldDataSchema(mm.Schema):
    class Meta:
        unknown = EXCLUDE

    title = fields.String(required=True, validate=not_empty)
    description = fields.String(missing='')
    is_required = fields.Bool(missing=False)
    input_type = fields.String(required=True, validate=not_empty)

    @pre_load
    def _remove_noise(self, data, **kwargs):
        # TODO remove this once the angular frontend is gone. we never allow enabling
        # or disabling a field here; that's handled in a separate request
        data = data.copy()
        data.pop('is_enabled', None)
        return data

    @validates('input_type')
    def _check_input_type(self, input_type, **kwargs):
        field = self.context['field']
        if field.input_type is not None and field.input_type != input_type:
            # TODO: when moving the frontend to react we should probably simply
            # stop sending it except when creating a new field and reject requests
            # that contain an input_type
            raise ValidationError('Cannot change field input type')
        if input_type not in get_field_types():
            raise ValidationError('Invalid field type')

    @post_load(pass_original=True)
    def _split_unknown(self, data, original_data, **kwargs):
        parsed = {k: v for k, v in data.items() if k in self.load_fields}
        unknown = {k: v for k, v in original_data.items() if k not in self.load_fields}
        unknown.pop('is_enabled', None)  # TODO: remove together with _remove_noise
        return parsed, unknown


class TextDataSchema(GeneralFieldDataSchema):
    class Meta(GeneralFieldDataSchema.Meta):
        exclude = ('is_required', 'input_type')


def _fill_form_field_with_data(field, field_data, is_static_text=False):
    schema_cls = TextDataSchema if is_static_text else GeneralFieldDataSchema
    schema = schema_cls(context={'field': field})
    general_data, raw_field_specific_data = schema.load(field_data)
    for key, value in general_data.items():
        setattr(field, key, value)
    if not is_static_text:
        schema = field.field_impl.create_setup_schema()
        field_specific_data = schema.load(raw_field_specific_data)
        if field.id is None:  # new field
            field.data, field.versioned_data = field.field_impl.process_field_data(field_specific_data)
        else:
            field.data, field.versioned_data = field.field_impl.process_field_data(field_specific_data, field.data,
                                                                                   field.versioned_data)


class RHManageRegFormFieldBase(RHManageRegFormSectionBase):
    """Base class for a specific field within a registration form."""

    field_class = RegistrationFormField
    normalize_url_spec = {
        'locators': {
            lambda self: self.field
        }
    }

    def _process_args(self):
        RHManageRegFormSectionBase._process_args(self)
        self.field = self.field_class.get_or_404(request.view_args['field_id'])


class RHRegistrationFormToggleFieldState(RHManageRegFormFieldBase):
    """Enable/Disable a field."""

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
    """Remove/Modify a field."""

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
    """Change position of a field within the section."""

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
        to_update = list(filter(fn, self.section.children))
        self.field.position = new_position
        for pos, field in enumerate(to_update, start_enum):
            field.position = pos
        db.session.flush()
        return jsonify()


class RHRegistrationFormAddField(RHManageRegFormSectionBase):
    """Add a field to the section."""

    def _process(self):
        field_data = snakify_keys(request.json['fieldData'])
        form_field = RegistrationFormField(parent_id=self.section.id, registration_form=self.regform)
        _fill_form_field_with_data(form_field, field_data)
        db.session.add(form_field)
        db.session.flush()
        return jsonify(view_data=form_field.view_data)


class RHRegistrationFormToggleTextState(RHRegistrationFormToggleFieldState):
    """Enable/Disable a static text field."""
    field_class = RegistrationFormText


class RHRegistrationFormModifyText(RHRegistrationFormModifyField):
    """Remove/Modify a static text field."""
    field_class = RegistrationFormText

    def _process_PATCH(self):
        field_data = snakify_keys(request.json['fieldData'])
        del field_data['input_type']
        _fill_form_field_with_data(self.field, field_data, is_static_text=True)
        return jsonify(view_data=self.field.view_data)


class RHRegistrationFormMoveText(RHRegistrationFormMoveField):
    """Change position of a static text field within the section."""
    field_class = RegistrationFormText


class RHRegistrationFormAddText(RHManageRegFormSectionBase):
    """Add a static text field to a section."""

    def _process(self):
        field_data = snakify_keys(request.json['fieldData'])
        del field_data['input_type']
        form_field = RegistrationFormText(parent_id=self.section.id, registration_form=self.regform)
        _fill_form_field_with_data(form_field, field_data, is_static_text=True)
        db.session.add(form_field)
        db.session.flush()
        return jsonify(view_data=form_field.view_data)
