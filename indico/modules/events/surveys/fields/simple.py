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

from wtforms.fields import IntegerField, BooleanField, StringField, TextAreaField
from wtforms.validators import NumberRange, Optional, ValidationError, Length, InputRequired

from indico.modules.events.surveys.fields.base import SurveyField, FieldConfigForm
from indico.util.i18n import _
from indico.web.forms.fields import IndicoStaticTextField, IndicoRadioField
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

    def get_summary(self):
        if not self.question.answers:
            return
        return [a.data for a in self.question.answers if a.data]

    def is_answer_empty(self, answer):
        return not answer.data


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
    required_validator = InputRequired

    @property
    def validators(self):
        min_value = self.question.field_data.get('min_value')
        max_value = self.question.field_data.get('max_value')
        if min_value is None and max_value is None:
            return
        return [NumberRange(min=min_value, max=max_value)]

    def get_summary(self):
        if not self.question.answers:
            return
        counter = Counter()
        for answer in self.question.answers:
            if answer.data:
                counter[answer.data] += 1
        total_answers = sum(counter.values())
        results = {'total': sum(counter.elements()),
                   'max': max(counter.elements()),
                   'min': min(counter.elements()),
                   'absolute': OrderedDict(sorted(counter.iteritems())),
                   'relative': OrderedDict((k, v / total_answers) for k, v in sorted(counter.iteritems()))}
        results['average'] = (results['max'] + results['min']) / len(list(counter.elements()))
        return results


class BoolField(SurveyField):
    name = 'bool'
    friendly_name = _('Yes/No')
    wtf_field_class = IndicoRadioField
    required_validator = InputRequired

    @property
    def wtf_field_kwargs(self):
        return {'orientation': 'horizontal',
                'choices': [(1, _('Yes')), (0, _('No'))],
                'coerce': lambda x: bool(int(x))}

    def get_summary(self):
        if not self.question.answers:
            return
        counter = Counter()
        for answer in self.question.answers:
            if answer.data is not None:
                counter[answer.data] += 1
        total = sum(counter.values())
        return {'total': total,
                'absolute': OrderedDict(((_('Yes'), counter[True]), (_('No'), counter[False]))),
                'relative': OrderedDict(((_('Yes'), counter[True] / total), (_('No'), counter[False] / total)))}

    def render_answer(self, answer):
        if answer is None:
            return ''
        return _('Yes') if answer else _('No')


class StaticTextConfigForm(FieldConfigForm):
    text = TextAreaField(_('Content'), description=_('Static text that will be shown to users. You can use Markdown to '
                                                     'format the text.'))


class SectionField(SurveyField):
    name = 'static_text'
    friendly_name = _('Section')
    is_section = True

    @classmethod
    def config_form(cls, *args, **kwargs):
        form = StaticTextConfigForm(*args, **kwargs)
        del form.description, form.is_required
        return form

    def create_wtf_field(self):
        raise RuntimeError('Section field cannot be rendered as a field')
