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

from wtforms.fields import IntegerField, BooleanField, StringField, SelectField
from wtforms.validators import NumberRange, Optional, ValidationError, Length, DataRequired

from indico.modules.events.surveys.fields.base import SurveyField, FieldConfigForm
from indico.util.i18n import _
from indico.web.forms.fields import IndicoRadioField, MultipleItemsField
from indico.web.forms.validators import HiddenUnless
from indico.web.forms.widgets import SwitchWidget


class TextConfigForm(FieldConfigForm):
    max_length = IntegerField(_('Max length'), [Optional(), NumberRange(min=1)])


class TextField(SurveyField):
    name = 'text'
    friendly_name = _('Text')
    config_form = TextConfigForm
    wtf_field_class = StringField

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
    wtf_field_class = BooleanField

    def create_wtf_field(self):
        return self._make_wtforms_field(self.wtf_field_class, widget=SwitchWidget())


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
    wtf_field_class = None

    def create_wtf_field(self):
        field_options = {}
        if self.question.field_data['display_type'] == 'select':
            self.wtf_field_class = SelectField
        else:
            self.wtf_field_class = IndicoRadioField
            field_options['orientation'] = self.question.field_data['radio_display_type']
        choices = [(iter['option'], iter['option']) for iter in self.question.field_data['options']]
        return self._make_wtforms_field(self.wtf_field_class, choices=choices, **field_options)


class TextParagraphConfigForm(IndicoForm):
    _common_fields = {'title'}

    title = StringField(_('Title'), [DataRequired()], description=_("The title of the field"))
    content = TextAreaField(_('Content'), description=_('Text content displayed in the field'))


class TextParagraphField(SurveyField):
    name = 'text_paragraph'
    friendly_name = _('Text Paragraph')
    config_form = TextParagraphConfigForm
    wtf_field_class = TextAreaField

    def create_wtf_field(self):
        return self._make_wtforms_field(self.wtf_field_class, default=self.question.field_data['content'])


class MultiSelectConfigForm(FieldConfigForm):
    choices = MultipleItemsField(_('choices'), [DataRequired()], fields=[('choice', _('Choice'))], unique_field='choice',
                                 description=_('Specify choices available for selection by user'))


class MultiSelectField(SurveyField):
    name = 'multiselect'
    friendly_name = _('Select multiple')
    config_form = MultiSelectConfigForm
    wtf_field_class = IndicoSelectMultipleCheckboxField

    def create_wtf_field(self):
        choices = [(choice['choice'], choice['choice']) for choice in self.question.field_data['choices']]
        return self._make_wtforms_field(self.wtf_field_class, choices=choices)
