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

from __future__ import unicode_literals, division

from collections import Counter, OrderedDict

from wtforms.fields import SelectField, IntegerField
from wtforms.validators import DataRequired, Optional, NumberRange, ValidationError, Length

from indico.modules.events.surveys.fields.base import SurveyField, FieldConfigForm
from indico.util.i18n import _, ngettext
from indico.web.forms.fields import IndicoRadioField, MultipleItemsField, IndicoSelectMultipleCheckboxField
from indico.web.forms.validators import HiddenUnless


class SingleChoiceConfigForm(FieldConfigForm):
    display_type = IndicoRadioField(_('Display type'), [DataRequired()],
                                    description=_('Widget that will be used to render the available options'),
                                    choices=[('radio', _('Radio buttons')),
                                             ('select', _('Drop-down list'))],
                                    default='radio')
    radio_display_type = IndicoRadioField(_('Alignment'),
                                          [DataRequired(), HiddenUnless('display_type', 'radio')],
                                          description=_('The arrangement of the options'),
                                          choices=[('vertical', _('Vertical')),
                                                   ('horizontal', _('Horizontal'))])
    options = MultipleItemsField(_('Options'), [DataRequired()],
                                 fields=[('option', _('Option'))], unique_field='option', uuid_field='id',
                                 description=_('Specify the answers the user can choose from'))


class _EmptyNoneSelectField(SelectField):
    def process_formdata(self, valuelist):
        super(_EmptyNoneSelectField, self).process_formdata(valuelist)
        if not self.data:
            self.data = None


class _EmptyNoneRadioField(IndicoRadioField):
    def process_formdata(self, valuelist):
        super(_EmptyNoneRadioField, self).process_formdata(valuelist)
        if not self.data:
            self.data = None


class SingleChoiceField(SurveyField):
    name = 'single_choice'
    friendly_name = _('Single Choice')
    config_form = SingleChoiceConfigForm

    def create_wtf_field(self):
        field_options = {'coerce': lambda x: x}
        choices = [(x['id'], x['option']) for x in self.question.field_data['options']]
        if self.question.field_data['display_type'] == 'select':
            field_class = _EmptyNoneSelectField
            choices = [('', '')] + choices
        else:
            field_class = _EmptyNoneRadioField
            field_options['orientation'] = self.question.field_data['radio_display_type']
            if field_options['orientation'] == 'vertical' and not self.question.is_required:
                field_options['default'] = ''
                choices = [('', _('No selection'))] + choices
        return self._make_wtforms_field(field_class, choices=choices, **field_options)

    def get_summary(self, include_empty=False):
        if not self.question.answers:
            return
        counter = Counter()
        for answer in self.question.answers:
            if answer.data is not None or include_empty:
                counter[answer.data] += 1
        total = sum(counter.values())
        options = self.question.field_data['options']
        return {'total': total,
                'absolute': OrderedDict((opt['option'], counter[opt['id']]) for opt in options),
                'relative': OrderedDict((opt['option'], counter[opt['id']] / total) for opt in options)}

    def render_answer(self, answer):
        question_options = {option_dict['id']: option_dict['option']
                            for option_dict in self.question.field_data['options']}
        return question_options.get(answer) or ''


class MultiSelectConfigForm(FieldConfigForm):
    options = MultipleItemsField(_('Options'), [DataRequired()], fields=[('option', _('Option'))],
                                 unique_field='option', uuid_field='id',
                                 description=_('Specify the answers the user can select'))
    min_choices = IntegerField(_('Min options'), [Optional(), NumberRange(min=0)],
                               description=_('The minimum number of options the user has to select. '
                                             'If the field is not marked as required, selecting zero options is always '
                                             'allowed and this check only applies if some options are selected.'))
    max_choices = IntegerField(_('Max options'), [Optional(), NumberRange(min=1)],
                               description=_('The maximum number of options the user may select.'))

    def _validate_min_max_choices(self):
        if (self.min_choices.data is not None and self.max_choices.data is not None and
                self.min_choices.data > self.max_choices.data):
            raise ValidationError(_('The min number of options must be less or equal than the max number of options.'))

    def validate_min_choices(self, field):
        if field.data is None:
            return
        self._validate_min_max_choices()
        if field.data >= len(self.options.data):
            raise ValidationError(_('The min number of options must be less than the total number of options.'))

    def validate_max_choices(self, field):
        if field.data is None:
            return
        self._validate_min_max_choices()
        if field.data > len(self.options.data):
            raise ValidationError(_('The max number of options must be less or equal than the total number of '
                                    'options.'))


class MultiSelectField(SurveyField):
    name = 'multiselect'
    friendly_name = _('Select multiple')
    config_form = MultiSelectConfigForm
    wtf_field_class = IndicoSelectMultipleCheckboxField

    @property
    def validators(self):
        min_choices = self.question.field_data.get('min_choices')
        max_choices = self.question.field_data.get('max_choices')
        if min_choices is None and max_choices is None:
            return
        if min_choices is None:
            min_choices = -1
        if max_choices is None:
            max_choices = -1
        if max_choices == -1:
            message = ngettext('Please select at least %(min)d option.',
                               'Please select at least %(min)d options.', min_choices)
        elif min_choices == -1:
            message = ngettext('Please select no more than %(max)d option.',
                               'Please select no more than %(max)d options.', max_choices)
        else:
            message = _('Please select between %(min)d and %(max)d options.')
        return [Length(min=min_choices, max=max_choices, message=message)]

    @property
    def wtf_field_kwargs(self):
        return {'choices': [(x['id'], x['option']) for x in self.question.field_data['options']],
                'coerce': lambda x: x}

    def get_summary(self):
        if not self.question.answers:
            return
        counter = Counter()
        for answer in self.question.answers:
            counter.update(answer.data)
        total = sum(counter.values())
        options = self.question.field_data['options']
        return {'total': total,
                'absolute': OrderedDict((opt['option'], counter[opt['id']]) for opt in options),
                'relative': OrderedDict((opt['option'], counter[opt['id']] / total) for opt in options)}

    def is_answer_empty(self, answer):
        return not answer.data

    def render_answer(self, answer):
        question_options = {option_dict['id']: option_dict['option']
                            for option_dict in self.question.field_data['options']}
        return [question_options[value] for value in answer if value in question_options]
