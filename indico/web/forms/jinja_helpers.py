# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import json

from wtforms.fields import BooleanField, RadioField
from wtforms.validators import Length, NumberRange
from wtforms.widgets.core import HiddenInput, Input, Select, TextArea

from indico.util.enum import RichEnum
from indico.web.forms.fields import (IndicoEnumRadioField, IndicoQuerySelectMultipleCheckboxField,
                                     IndicoSelectMultipleCheckboxField)
from indico.web.forms.validators import (ConfirmPassword, HiddenUnless, IndicoRegexp, SecurePassword, SoftLength,
                                         WordCount)
from indico.web.forms.widgets import RemoteDropdownWidget, TypeaheadWidget


def is_single_line_field(field):
    if isinstance(field.widget, (RemoteDropdownWidget, TypeaheadWidget)):
        return True
    if isinstance(field.widget, Select):
        return not field.widget.multiple
    if isinstance(field.widget, Input):
        return field.widget.input_type not in {'checkbox', 'radio', 'hidden'}
    if isinstance(field.widget, TextArea):
        return True
    return getattr(field.widget, 'single_line', False)


def _attrs_for_validators(field, validators):
    attrs = {}
    for validator in validators:
        if isinstance(validator, WordCount):
            if validator.min >= 0:
                attrs['data-min-words'] = validator.min
            if validator.max >= 0:
                attrs['data-max-words'] = validator.max
        elif isinstance(validator, SoftLength):
            # XXX: SoftLength is a Length subclass so it must be checked first
            if validator.min >= 0:
                attrs['data-min-length'] = validator.min
            if validator.max >= 0:
                attrs['data-max-length'] = validator.max
        elif isinstance(validator, Length):
            if validator.min >= 0:
                attrs['minlength'] = validator.min
            if validator.max >= 0:
                attrs['maxlength'] = validator.max
        elif isinstance(validator, SecurePassword):
            attrs['minlength'] = validator.MIN_LENGTH
        elif isinstance(validator, IndicoRegexp) and validator.client_side:
            attrs['pattern'] = validator.regex.pattern
        elif isinstance(validator, NumberRange):
            if validator.min is not None:
                attrs['min'] = validator.min
            if validator.max is not None:
                attrs['max'] = validator.max
        elif isinstance(validator, ConfirmPassword):
            attrs['data-confirm-password'] = field.get_form()[validator.fieldname].name
        elif isinstance(validator, HiddenUnless):
            condition_field = field.get_form()[validator.field]
            checked_only = isinstance(condition_field, (RadioField, BooleanField, IndicoEnumRadioField))
            val = validator.value
            if val is None:
                val = []
            elif not isinstance(val, (set, list, tuple)):
                val = [val]
            values = [(v.name if isinstance(v, RichEnum) else v) for v in val]

            attrs['data-hidden-unless'] = json.dumps({'field': condition_field.name,
                                                      'values': values,
                                                      'checked_only': checked_only})
    return attrs


def render_field(field, widget_attrs, disabled=None):
    """Render a WTForms field, taking into account validators."""
    if not widget_attrs.get('placeholder'):
        widget_attrs = dict(widget_attrs)
        widget_attrs.pop('placeholder', None)
    args = _attrs_for_validators(field, field.validators)
    args['required'] = (bool(field.flags.required) and not field.flags.conditional and
                        not isinstance(field, (IndicoSelectMultipleCheckboxField,
                                               IndicoQuerySelectMultipleCheckboxField)))
    args.update(widget_attrs)
    if disabled is not None:
        args['disabled'] = disabled
    return field(**args)


def iter_form_fields(form, fields=None, skip=None, hidden_fields=False):
    """Iterate over the fields in a WTForm.

    :param fields: If specified only fields that are in this list are
                   yielded. This also overrides the field order.
    :param skip: If specified, only fields NOT in this set/list are
                 yielded.
    :param hidden_fields: How to handle hidden fields. Setting this to
                          ``True`` or ``False`` will yield only hidden
                          or non-hidden fields.  Setting it to ``None``
                          will yield all fields.
    """
    if fields is not None:
        field_iter = (form[field_name] for field_name in fields if field_name in form)
    else:
        field_iter = iter(form)
    if skip:
        skip = set(skip)
        field_iter = (field for field in field_iter if field.short_name not in skip)
    if hidden_fields is not None:
        field_iter = (field for field in field_iter if isinstance(field.widget, HiddenInput) == hidden_fields)
    yield from field_iter
