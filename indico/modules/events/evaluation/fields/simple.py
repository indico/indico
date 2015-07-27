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

from wtforms.fields import IntegerField, BooleanField, StringField
from wtforms.validators import NumberRange, Optional, ValidationError, Length

from indico.modules.events.evaluation.fields.base import EvaluationField, FieldConfigForm
from indico.util.i18n import _
from indico.web.forms.widgets import SwitchWidget


class TextConfigForm(FieldConfigForm):
    max_length = IntegerField(_('Max length'), [Optional(), NumberRange(min=1)])


class TextField(EvaluationField):
    name = 'text'
    friendly_name = _('Text')
    config_form = TextConfigForm

    def get_wtforms_field(self):
        max_length = self.question.field_data.get('max_length')
        validators = [Length(max=max_length)] if max_length else None
        return self._make_wtforms_field(StringField, validators)


class NumberConfigForm(FieldConfigForm):
    min_value = IntegerField(_('Min value'))
    max_value = IntegerField(_('Max value'))

    def _validate_min_max_value(self, field):
        if self.min_value.data >= self.max_value.data:
            raise ValidationError(_('The min value must be less than the max value.'))

    validate_min_value = _validate_min_max_value
    validate_max_value = _validate_min_max_value


class NumberField(EvaluationField):
    name = 'number'
    friendly_name = _('Number')
    config_form = NumberConfigForm

    def get_wtforms_field(self):
        min_value = self.question.field_data.get('min_value')
        max_value = self.question.field_data.get('max_value')
        validators = [NumberRange(min=min_value, max=max_value)]
        # XXX: do we need to support floats? in that case add another config option
        # to determine whether to use IntegerField or FloatField
        return self._make_wtforms_field(IntegerField, validators)


class BoolField(EvaluationField):
    name = 'bool'
    friendly_name = _('Yes/No')

    def get_wtforms_field(self):
        return self._make_wtforms_field(BooleanField, widget=SwitchWidget())
