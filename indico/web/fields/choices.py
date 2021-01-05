# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import division, unicode_literals

from wtforms.fields import SelectField
from wtforms.fields.html5 import IntegerField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError

from indico.util.i18n import _, ngettext
from indico.web.fields.base import BaseField
from indico.web.forms.fields import IndicoRadioField, IndicoSelectMultipleCheckboxField, MultiStringField
from indico.web.forms.validators import HiddenUnless


class _ChoiceFieldBase(BaseField):
    def copy_field_data(self):
        """
        Return a copy of the field's configuration data without
        the IDs used to identify selected options.
        """
        field_data_copy = super(_ChoiceFieldBase, self).copy_field_data()
        for option in field_data_copy['options']:
            del option['id']
        return field_data_copy


class SingleChoiceConfigForm(object):
    display_type = IndicoRadioField(_('Display type'), [DataRequired()],
                                    description=_('Widget that will be used to render the available options'),
                                    choices=[('radio', _('Radio buttons')),
                                             ('select', _('Drop-down list'))],
                                    default='radio')
    radio_display_type = IndicoRadioField(_('Alignment'),
                                          [HiddenUnless('display_type', 'radio'), DataRequired()],
                                          description=_('The arrangement of the options'),
                                          choices=[('vertical', _('Vertical')),
                                                   ('horizontal', _('Horizontal'))])
    options = MultiStringField(_('Options'), [DataRequired()], field=('option', _('option')), unique=True,
                               uuid_field='id', sortable=True,
                               description=_('Specify the options the user can choose from'))


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


class SingleChoiceField(_ChoiceFieldBase):
    name = 'single_choice'
    friendly_name = _('Single Choice')
    config_form = SingleChoiceConfigForm
    log_type = 'string'

    def create_wtf_field(self):
        field_options = {'coerce': lambda x: x}
        choices = [(x['id'], x['option']) for x in self.object.field_data['options']]
        if self.object.field_data['display_type'] == 'select':
            field_class = _EmptyNoneSelectField
            choices = [('', '')] + choices
        else:
            field_class = _EmptyNoneRadioField
            field_options['orientation'] = self.object.field_data['radio_display_type']
            if field_options['orientation'] == 'vertical' and not self.object.is_required:
                field_options['default'] = ''
                choices = [('', _('No selection'))] + choices
        return self._make_wtforms_field(field_class, choices=choices, **field_options)

    def is_value_empty(self, value):
        # No selection is also a valid option
        return False

    def get_friendly_value(self, value):
        option_map = {option_dict['id']: option_dict['option'] for option_dict in self.object.field_data['options']}
        return option_map.get(value) or ''


class MultiSelectConfigForm(object):
    options = MultiStringField(_('Options'), [DataRequired()], field=('option', _('option')), unique=True,
                               uuid_field='id', sortable=True, description=_('Specify the answers the user can select'))
    min_choices = IntegerField(_("Minimum choices"), [HiddenUnless('is_required'), Optional(), NumberRange(min=0)],
                               description=_("The minimum amount of options the user has to choose."))
    max_choices = IntegerField(_("Maximum choices"), [HiddenUnless('is_required'), Optional(), NumberRange(min=1)],
                               description=_("The maximum amount of options the user may choose."))

    def _validate_min_max_choices(self):
        if (self.min_choices.data is not None and self.max_choices.data is not None and
                self.min_choices.data > self.max_choices.data):
            raise ValidationError(_('Maximum choices must be greater than minimum choices.'))

    def validate_min_choices(self, field):
        if field.data is None:
            return
        if field.data >= len(self.options.data):
            raise ValidationError(_("Minimum choices must be fewer than the total number of options."))

    def validate_max_choices(self, field):
        if field.data is None:
            return
        self._validate_min_max_choices()
        if field.data > len(self.options.data):
            raise ValidationError(_("Maximum choices must be fewer or equal than the total number of options."))


class MultiSelectField(_ChoiceFieldBase):
    name = 'multiselect'
    friendly_name = _('Select multiple')
    config_form = MultiSelectConfigForm
    wtf_field_class = IndicoSelectMultipleCheckboxField
    log_type = 'list'

    @property
    def validators(self):
        min_choices = self.object.field_data.get('min_choices')
        max_choices = self.object.field_data.get('max_choices')
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
        return {'choices': [(x['id'], x['option']) for x in self.object.field_data['options']],
                'coerce': lambda x: x}

    def get_friendly_value(self, value):
        option_map = {option_dict['id']: option_dict['option'] for option_dict in self.object.field_data['options']}
        return [option_map[id_] for id_ in value if id_ in option_map]
