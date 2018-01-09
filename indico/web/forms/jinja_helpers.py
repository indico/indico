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

import json

from wtforms.fields import BooleanField, RadioField
from wtforms.validators import Length, NumberRange
from wtforms.widgets.core import HiddenInput, Input, Select, TextArea

from indico.util.struct.enum import RichEnum
from indico.web.forms.fields import (IndicoEnumRadioField, IndicoQuerySelectMultipleCheckboxField,
                                     IndicoSelectMultipleCheckboxField)
from indico.web.forms.validators import ConfirmPassword, HiddenUnless, IndicoRegexp, SoftLength, WordCount
from indico.web.forms.widgets import SelectizeWidget, TypeaheadWidget


def is_single_line_field(field):
    if isinstance(field.widget, (SelectizeWidget, TypeaheadWidget)):
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
    """Renders a WTForms field, taking into account validators"""
    if not widget_attrs.get('placeholder'):
        widget_attrs = dict(widget_attrs)
        widget_attrs.pop('placeholder', None)
    args = _attrs_for_validators(field, field.validators)
    args['required'] = (field.flags.required and not field.flags.conditional and
                        not isinstance(field, (IndicoSelectMultipleCheckboxField,
                                               IndicoQuerySelectMultipleCheckboxField)))
    args.update(widget_attrs)
    if disabled is not None:
        args['disabled'] = disabled
    return field(**args)


def iter_form_fields(form, fields=None, skip=None, hidden_fields=False):
    """Iterates over the fields in a WTForm

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
    for field in field_iter:
        yield field
