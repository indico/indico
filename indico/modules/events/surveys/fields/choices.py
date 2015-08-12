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

from wtforms.fields import SelectField
from wtforms.validators import DataRequired

from indico.modules.events.surveys.fields.base import SurveyField, FieldConfigForm
from indico.util.i18n import _
from indico.web.forms.fields import IndicoRadioField, MultipleItemsField, IndicoSelectMultipleCheckboxField
from indico.web.forms.validators import HiddenUnless


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
                                 fields=[('option', _('Option'))], unique_field='option', uuid_field='id',
                                 description=_('Specify the answers the user can choose from'))


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
        choices = [(x['id'], x['option']) for x in self.question.field_data['options']]
        return self._make_wtforms_field(field_class, choices=choices, **field_options)


class MultiSelectConfigForm(FieldConfigForm):
    options = MultipleItemsField(_('Options'), [DataRequired()], fields=[('option', _('Option'))],
                                 unique_field='option', uuid_field='id',
                                 description=_('Specify the answers the user can select'))


class MultiSelectField(SurveyField):
    name = 'multiselect'
    friendly_name = _('Select multiple')
    config_form = MultiSelectConfigForm

    def create_wtf_field(self):
        choices = [(x['id'], x['option']) for x in self.question.field_data['options']]
        return self._make_wtforms_field(IndicoSelectMultipleCheckboxField, choices=choices)
