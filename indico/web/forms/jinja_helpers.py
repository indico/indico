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

import re

from wtforms.widgets.core import Input, Select
from wtforms.validators import Length, Regexp, NumberRange

from indico.web.forms.validators import ConfirmPassword


def is_single_line_field(field):
    if isinstance(field.widget, Select):
        return not field.widget.multiple
    if isinstance(field.widget, Input):
        return field.widget.input_type not in {'checkbox', 'radio', 'hidden'}
    return getattr(field.widget, 'single_line', False)


def _attrs_for_validators(field, validators):
    attrs = {}
    for validator in validators:
        if isinstance(validator, Length):
            if validator.min >= 0:
                attrs['minlength'] = validator.min
            if validator.max >= 0:
                attrs['maxlength'] = validator.max
        elif isinstance(validator, Regexp):
            attrs['pattern'] = validator.regex.pattern
        elif isinstance(validator, NumberRange):
            if validator.min is not None:
                attrs['min'] = validator.min
            if validator.max is not None:
                attrs['max'] = validator.max
        elif isinstance(validator, ConfirmPassword):
            # We don't have access to the form so we need to get the
            # form's prefix from this field's name...
            prefix = ''
            if field.name != field.short_name:
                prefix = re.sub(re.escape(field.short_name) + '$', '', field.name, 1)
            attrs['data-confirm-password'] = prefix + validator.fieldname
    return attrs


def render_field(field, widget_attrs):
    """Renders a WTForms field, taking into account validators"""
    args = _attrs_for_validators(field, field.validators)
    args['required'] = field.flags.required and not field.flags.conditional
    args.update(widget_attrs)
    return field(**args)
