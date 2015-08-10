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

from wtforms.fields import IntegerField, BooleanField, StringField, SelectField, TextAreaField
from wtforms.validators import NumberRange, Optional, ValidationError, Length, DataRequired

from indico.modules.events.surveys.fields.base import SurveyField, FieldConfigForm
from indico.util.i18n import _
from indico.web.forms.fields import IndicoRadioField, MultipleItemsField, IndicoSelectMultipleCheckboxField
from indico.web.forms.validators import HiddenUnless
from indico.web.forms.widgets import SwitchWidget


class TextConfigForm(FieldConfigForm):
    max_length = IntegerField(_('Max length'), [Optional(), NumberRange(min=1)])
    multiline = BooleanField(_('Multiline'), widget=SwitchWidget(),
                             description=_("If the field should be rendered as a textarea instead of a single-line "
                                           "text field."))


class TextField(SurveyField):
    name = 'text'
    friendly_name = _('Text')
    config_form = TextConfigForm

    @property
    def wtf_field_class(self):
        return TextAreaField if self.question.field_data.get('multiline') else StringField

    @property
    def validators(self):
        max_length = self.question.field_data.get('max_length')
        return [Length(max=max_length)] if max_length else None


class NumberConfigForm(FieldConfigForm):
    min_value = IntegerField(_('Min value'), [Optional()])
    max_value = IntegerField(_('Max value'), [Optional()])

    def _validate_min_max_value(self, field):
        if (self.min_value.data is not None and self.max_value.data is not None and
                self.min_value.data >= self.max_value.data):
            raise ValidationError(_('The min value must be less than the max value.'))

    validate_min_value = _validate_min_max_value
    validate_max_value = _validate_min_max_value


class NumberField(SurveyField):
    name = 'number'
    friendly_name = _('Number')
    config_form = NumberConfigForm
    wtf_field_class = IntegerField

    @property
    def validators(self):
        min_value = self.question.field_data.get('min_value')
        max_value = self.question.field_data.get('max_value')
        return [NumberRange(min=min_value, max=max_value)]


class BoolField(SurveyField):
    name = 'bool'
    friendly_name = _('Yes/No')

    def create_wtf_field(self):
        return self._make_wtforms_field(BooleanField, widget=SwitchWidget())


class SingleChoiceConfigForm(FieldConfigForm):
    display_type = IndicoRadioField(_('Display type'), [DataRequired()],
                                    description=_('Show the question either as radio button or select'),
                                    choices=[('radio', _('Show as radio button')),
                                             ('select', _('Show as select field'))],
                                    default='radio')
    radio_display_type = IndicoRadioField(_('Arrangment of available options'),
                                          [HiddenUnless('display_type', 'radio')],
                                          choices=[('vertical', _('Vertical alignment')),
                                                   ('horizontal', _('Horizontal alignment'))])
    options = MultipleItemsField(_('Options'), [DataRequired()],
                                 fields=[('option', _('Option'))], unique_field='option',
                                 description=_('Specify options available for selection by user'))


class SingleChoiceField(SurveyField):
    name = 'single_choice'
    friendly_name = _('Single Choice')
    config_form = SingleChoiceConfigForm

    def create_wtf_field(self):
        field_options = {}
        if self.question.field_data['display_type'] == 'select':
            field_class = SelectField
        else:
            field_class = IndicoRadioField
            field_options['orientation'] = self.question.field_data['radio_display_type']
        options = [x['option'] for x in self.question.field_data['options']]
        choices = zip(options, options)
        return self._make_wtforms_field(field_class, choices=choices, **field_options)


class MultiSelectConfigForm(FieldConfigForm):
    options = MultipleItemsField(_('Options'), [DataRequired()], fields=[('option', _('Option'))],
                                 unique_field='option',
                                 description=_('Specify choices available for selection by user'))


class MultiSelectField(SurveyField):
    name = 'multiselect'
    friendly_name = _('Select multiple')
    config_form = MultiSelectConfigForm

    def create_wtf_field(self):
        options = [x['option'] for x in self.question.field_data['options']]
        choices = zip(options, options)
        return self._make_wtforms_field(IndicoSelectMultipleCheckboxField, choices=choices)
