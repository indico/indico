# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import timedelta

from flask import jsonify, request, session
from marshmallow import EXCLUDE, ValidationError, fields, post_load, validates, validates_schema
from werkzeug.exceptions import BadRequest

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.core.errors import NoReportError
from indico.core.marshmallow import mm
from indico.modules.events.registration import logger
from indico.modules.events.registration.controllers.management.sections import RHManageRegFormSectionBase
from indico.modules.events.registration.fields import get_field_types
from indico.modules.events.registration.models.form_fields import RegistrationFormField
from indico.modules.events.registration.models.items import RegistrationFormItemType, RegistrationFormText
from indico.modules.events.registration.util import get_flat_section_positions_setup_data, update_regform_item_positions
from indico.modules.events.settings import data_retention_settings
from indico.modules.logs.models.entries import EventLogRealm, LogKind
from indico.modules.logs.util import make_diff_log
from indico.util.date_time import format_human_timedelta
from indico.util.i18n import _, ngettext
from indico.util.marshmallow import not_empty
from indico.util.string import snakify_keys


class GeneralFieldDataSchema(mm.Schema):
    class Meta:
        unknown = EXCLUDE

    title = fields.String(required=True, validate=not_empty)
    description = fields.String(load_default='')
    is_required = fields.Bool(load_default=False)
    retention_period = fields.TimeDelta(load_default=None, precision=fields.TimeDelta.WEEKS)
    input_type = fields.String(required=True, validate=not_empty)
    show_if_id = fields.Integer(required=False, load_default=None, data_key='show_if_field_id')
    show_if_values = fields.List(fields.Raw(), required=False, data_key='show_if_field_values')

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

    @validates('retention_period')
    def _check_retention_period(self, retention_period, **kwargs):
        field = self.context['field']
        with db.session.no_autoflush:
            min_retention_period = data_retention_settings.get('minimum_data_retention')
            max_retention_period = data_retention_settings.get('maximum_data_retention')
        if retention_period is not None:
            if field.type == RegistrationFormItemType.field_pd and field.personal_data_type.is_required:
                raise ValidationError('Cannot add retention period to required field')

            regform_retention_period = field.registration_form.retention_period
            if regform_retention_period and retention_period > regform_retention_period:
                raise ValidationError(_('Retention period cannot be longer than that of the registration form'),
                                      'retention_period')
            if retention_period < min_retention_period:
                raise ValidationError(ngettext('The retention period cannot be less than {} week.',
                                               'The retention period cannot be less than {} weeks.',
                                               min_retention_period.days // 7)
                                      .format(min_retention_period.days // 7))
            elif max_retention_period and retention_period > max_retention_period:
                raise ValidationError(ngettext('The retention period cannot be longer than {} week.',
                                               'The retention period cannot be longer than {} weeks.',
                                               max_retention_period.days // 7)
                                      .format(max_retention_period.days // 7))
            elif not max_retention_period and retention_period > timedelta(3650):
                raise ValidationError(_('The retention period cannot be longer than 10 years. Leave the field empty '
                                        'for indefinite.'))

    @validates('show_if_id')
    @no_autoflush
    def _check_show_if_id(self, field_id, **kwargs):
        from indico.modules.events.registration.models.form_fields import RegistrationFormItem
        if field_id is None:
            return
        field = self.context['field']
        if field.parent.is_manager_only:
            raise ValueError('Manager-only fields cannot be conditionally shown')
        used_field_ids = set()
        if field.id is not None:
            if field.id == field_id:
                raise ValueError('The field cannot conditionally depend on itself to be shown')
            used_field_ids.add(field.id)
        regform = self.context['regform']
        if not (condition_field := RegistrationFormItem.query.with_parent(regform).filter_by(id=field_id).first()):
            raise ValidationError('The field to show does not belong to the same registration form.')
        if not condition_field.field_impl.allow_condition:
            raise ValidationError('This field cannot be used as a condition.')
        # Avoid cycles
        next_field_id = field_id
        while next_field_id is not None:
            if next_field_id in used_field_ids:
                raise ValidationError('Field conditions may not have cycles (a -> b -> c -> a)')
            else:
                used_field_ids.add(next_field_id)
            next_field = RegistrationFormItem.query.filter_by(id=next_field_id).one()
            if next_field.parent.is_manager_only:
                raise ValidationError('Field conditions may not depend on fields in manager-only sections')
            if not next_field.is_enabled:
                raise ValidationError('Field conditions may not depend on disabled fields')
            next_field_id = next_field.show_if_id

    @validates_schema(skip_on_field_errors=True)
    @no_autoflush
    def _validate_conditions_retention_period(self, data, **kwargs):
        from indico.modules.events.registration.models.form_fields import RegistrationFormItem
        if isinstance(self, TextDataSchema):
            # for static text we have no retention period
            return
        regform = self.context['regform']
        show_if_id = data['show_if_id']
        retention_period = data['retention_period']
        # check upstream fields
        if show_if_id is not None:
            condition_field = RegistrationFormItem.query.with_parent(regform).filter_by(id=show_if_id).one()
            for field in {condition_field, *condition_field.show_if_field_transitive}:
                if field.retention_period and (not retention_period or field.retention_period < retention_period):
                    raise ValidationError(
                        _('This field depends on "{field}", which has a shorter retention period ({period}).')
                        .format(field=field.title, period=format_human_timedelta(field.retention_period, 'weeks',
                                                                                 weeks=True)),
                        'retention_period',
                    )
        # check downstream fields
        for field in self.context['field'].condition_for_transitive:
            if isinstance(field, RegistrationFormText):
                continue
            # this field has a retention period, and the downstream field doesn't
            if retention_period and not field.retention_period:
                raise ValidationError(
                    _('This field is a condition for "{field}", which has a longer retention period (indefinite).')
                    .format(field=field.title),
                    'retention_period',
                )
            # this field has a retention period that's lower than that of the downstream field
            if field.retention_period and retention_period and field.retention_period > retention_period:
                raise ValidationError(
                    _('This field is a condition for "{field}", which has a longer retention period ({period}).')
                    .format(field=field.title, period=format_human_timedelta(field.retention_period, 'weeks',
                                                                             weeks=True)),
                    'retention_period',
                )

    @post_load(pass_original=True)
    def _postprocess(self, data, original_data, **kwargs):
        # clear show_if_values if there's no show_if_id
        if data['show_if_id'] is None:
            data['show_if_values'] = None
        # split result into parsed and unknown values
        load_orig_keys = {f.data_key or k for k, f in self.load_fields.items()}
        parsed = {k: v for k, v in data.items() if k in self.load_fields}
        unknown = {k: v for k, v in original_data.items() if k not in load_orig_keys}
        return parsed, unknown


class TextDataSchema(GeneralFieldDataSchema):
    class Meta(GeneralFieldDataSchema.Meta):
        exclude = ('is_required', 'retention_period', 'input_type')


def _fill_form_field_with_data(field, field_data, *, is_static_text=False):
    context = {'regform': field.registration_form, 'field': field}
    schema_cls = TextDataSchema if is_static_text else GeneralFieldDataSchema
    schema = schema_cls(context=context)
    general_data, raw_field_specific_data = schema.load(field_data)
    changes = {}
    for key, value in general_data.items():
        old_value = getattr(field, key)
        if old_value != value:
            changes[key] = (old_value, value)
        setattr(field, key, value)
    if not is_static_text:
        schema = field.field_impl.create_setup_schema(context=context)
        field_specific_data = schema.load(raw_field_specific_data)
        if field.id is None:  # new field
            field.data, field.versioned_data = field.field_impl.process_field_data(field_specific_data)
        else:
            field.data, field.versioned_data = field.field_impl.process_field_data(field_specific_data, field.data,
                                                                                   field.versioned_data)
    return changes


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
        if not enabled and self.field.condition_for:
            raise NoReportError.wrap_exc(BadRequest(_('Fields used as conditional cannot be disabled')))
        self.field.is_enabled = enabled
        update_regform_item_positions(self.regform)
        db.session.flush()
        logger.info('Field %s modified by %s', self.field, session.user)
        if enabled:
            self.field.log(
                EventLogRealm.management, LogKind.positive, 'Registration',
                f'Field "{self.field.title}" in "{self.regform.title}" enabled', session.user
            )
        else:
            self.field.log(
                EventLogRealm.management, LogKind.negative, 'Registration',
                f'Field "{self.field.title}" in "{self.regform.title}" disabled', session.user
            )
        return jsonify(view_data=self.field.view_data, positions=get_flat_section_positions_setup_data(self.regform))


class RHRegistrationFormModifyField(RHManageRegFormFieldBase):
    """Remove/Modify a field."""

    def _process_DELETE(self):
        if self.field.type == RegistrationFormItemType.field_pd:
            raise BadRequest
        if self.field.condition_for:
            raise NoReportError.wrap_exc(BadRequest(_('Fields used as conditional cannot be deleted')))
        signals.event.registration_form_field_deleted.send(self.field)
        self.field.is_deleted = True
        self.field.show_if_id = None
        self.field.show_if_values = None
        update_regform_item_positions(self.regform)
        db.session.flush()
        self.field.log(
            EventLogRealm.management, LogKind.negative, 'Registration',
            f'Field "{self.field.title}" in "{self.regform.title}" deleted', session.user
        )
        logger.info('Field %s deleted by %s', self.field, session.user)
        return jsonify()

    def _process_PATCH(self):
        field_data = snakify_keys(request.json['fieldData'])
        if self.field.type == RegistrationFormItemType.field_pd and self.field.personal_data_type.is_required:
            field_data['is_required'] = True
        elif 'input_type' in field_data and self.field.input_type != field_data['input_type']:
            raise BadRequest
        field_data['input_type'] = self.field.input_type
        changes = _fill_form_field_with_data(self.field, field_data)
        changes = make_diff_log(changes, {
            'title': {'title': 'Title', 'type': 'string'},
            'description': {'title': 'Description'},
            'is_required': {'title': 'Required'},
            'retention_period': {'title': 'Retention period'},
        })
        self.field.log(
            EventLogRealm.management, LogKind.change, 'Registration',
            f'Field "{self.field.title}" in "{self.regform.title}" modified', session.user,
            data={'Changes': changes}
        )
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
        form_field = RegistrationFormField(parent=self.section, registration_form=self.regform)
        _fill_form_field_with_data(form_field, field_data)
        db.session.add(form_field)
        db.session.flush()
        form_field.log(
            EventLogRealm.management, LogKind.positive, 'Registration',
            f'Field "{form_field.title}" in "{self.regform.title}" added', session.user,
            data={'Type': form_field.input_type}
        )
        return jsonify(view_data=form_field.view_data)


class RHRegistrationFormToggleTextState(RHRegistrationFormToggleFieldState):
    """Enable/Disable a static text field."""

    field_class = RegistrationFormText


class RHRegistrationFormModifyText(RHRegistrationFormModifyField):
    """Remove/Modify a static text field."""

    field_class = RegistrationFormText

    def _process_PATCH(self):
        field_data = snakify_keys(request.json['fieldData'])
        field_data.pop('input_type', None)
        changes = _fill_form_field_with_data(self.field, field_data, is_static_text=True)
        changes = make_diff_log(changes, {
            'title': {'title': 'Title', 'type': 'string'},
            'description': {'title': 'Description'},
        })
        self.field.log(
            EventLogRealm.management, LogKind.change, 'Registration',
            f'Field "{self.field.title}" in "{self.regform.title}" modified', session.user,
            data={'Changes': changes}
        )
        return jsonify(view_data=self.field.view_data)


class RHRegistrationFormMoveText(RHRegistrationFormMoveField):
    """Change position of a static text field within the section."""

    field_class = RegistrationFormText


class RHRegistrationFormAddText(RHManageRegFormSectionBase):
    """Add a static text field to a section."""

    def _process(self):
        field_data = snakify_keys(request.json['fieldData'])
        del field_data['input_type']
        form_field = RegistrationFormText(parent=self.section, registration_form=self.regform)
        _fill_form_field_with_data(form_field, field_data, is_static_text=True)
        db.session.add(form_field)
        db.session.flush()
        form_field.log(
            EventLogRealm.management, LogKind.positive, 'Registration',
            f'Field "{form_field.title}" in "{self.regform.title}" added', session.user,
            data={'Type': 'label'}
        )
        return jsonify(view_data=form_field.view_data)
