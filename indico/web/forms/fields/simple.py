# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import json

from markupsafe import escape
from wtforms import ValidationError
from wtforms.fields import (BooleanField, Field, HiddenField, PasswordField, RadioField, SelectMultipleField,
                            TextAreaField)
from wtforms.widgets import CheckboxInput

from indico.modules.events.registration.models.registrations import PublishRegistrationsMode
from indico.util.i18n import _
from indico.util.string import sanitize_email, validate_email
from indico.web.forms.fields.util import is_preprocessed_formdata
from indico.web.forms.widgets import DropdownWidget, HiddenInputs, JinjaWidget, PasswordWidget


class IndicoSelectMultipleCheckboxField(SelectMultipleField):
    widget = JinjaWidget('forms/checkbox_group_widget.html', single_kwargs=True)
    option_widget = CheckboxInput()

    class _Option(SelectMultipleField._Option):
        def __init__(self, *args, **kwargs):
            # WTForms 3 started passing validators to the sub-options, but this resulted
            # in the `required` flag to be set for the choices in various subclasses of
            # this field when using custom widgets (in some of the plugins). Removing
            # the validators avoids this, and in case of a checkbox there's nothing to
            # "validate" in the child items anyway.
            kwargs.pop('validators', None)
            super().__init__(*args, **kwargs)


class IndicoSelectMultipleCheckboxBooleanField(IndicoSelectMultipleCheckboxField):
    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)
        values = set(self.data)
        self.data = {x[0]: x[0] in values for x in self.choices}

    def iter_choices(self):
        for value, label in self.choices:
            selected = self.data is not None and self.data.get(self.coerce(value))
            yield (value, label, selected, {})


class IndicoButtonsBooleanField(BooleanField):
    widget = JinjaWidget('forms/buttons_boolean_widget.html', single_kwargs=True, single_line=True)

    def __init__(self, *args, **kwargs):
        self.true_caption = kwargs.pop('true_caption')
        self.false_caption = kwargs.pop('false_caption')
        super().__init__(*args, **kwargs)


class IndicoRadioField(RadioField):
    widget = JinjaWidget('forms/radio_buttons_widget.html', single_kwargs=True)

    def __init__(self, *args, **kwargs):
        self.option_orientation = kwargs.pop('orientation', 'vertical')
        super().__init__(*args, **kwargs)


class JSONField(HiddenField):
    #: Whether an object may be populated with the data from this field
    CAN_POPULATE = False

    def __init__(self, *args, empty_if_null=False, **kwargs):
        self.empty_if_null = empty_if_null
        super().__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        if is_preprocessed_formdata(valuelist):
            self.data = valuelist[0]
        elif valuelist:
            self.data = json.loads(valuelist[0])

    def _value(self):
        return '' if self.data is None and self.empty_if_null else json.dumps(self.data)

    def populate_obj(self, obj, name):
        if self.CAN_POPULATE:
            super().populate_obj(obj, name)


class HiddenFieldList(HiddenField):
    """A hidden field that handles lists of strings.

    This is done `getlist`-style, i.e. by repeating the input element
    with the same name for each list item.

    The only case where this field is useful is when you display a
    form via POST and provide a list of items (e.g. ids) related
    to the form which needs to be kept when the form is submitted and
    also need to access it via ``request.form.getlist(...)`` before
    submitting the form.
    """

    widget = HiddenInputs()

    def process_formdata(self, valuelist):
        self.data = valuelist

    def _value(self):
        return self.data


class TextListField(TextAreaField):
    def process_formdata(self, valuelist):
        if valuelist:
            self.data = [line.strip() for line in valuelist[0].split('\n') if line.strip()]
        else:
            self.data = []

    def _validate_item(self, line):
        pass

    def pre_validate(self, form):
        for line in self.data:
            self._validate_item(line)

    def _value(self):
        return '\n'.join(self.data) if self.data else ''


class EmailListField(TextListField):
    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)
        self.data = list(map(sanitize_email, self.data))

    def _validate_item(self, line):
        if not validate_email(line):
            raise ValidationError(_('Invalid email address: {}').format(escape(line)))


class IndicoPasswordField(PasswordField):
    """Password field which can show or hide the password."""

    widget = PasswordWidget()

    def __init__(self, *args, **kwargs):
        self.toggle = kwargs.pop('toggle', False)
        super().__init__(*args, **kwargs)


class IndicoStaticTextField(Field):
    """Return an html element with text taken from this field's value."""

    widget = JinjaWidget('forms/static_text_widget.html')

    def __init__(self, *args, **kwargs):
        self.text_value = kwargs.pop('text', '')
        super().__init__(*args, **kwargs)

    def process_data(self, data):
        self.text_value = self.data = str(data)

    def _value(self):
        return self.text_value


class IndicoEmailRecipientsField(Field):
    widget = JinjaWidget('forms/email_recipients_widget.html', single_kwargs=True)

    def process_data(self, data):
        self.data = sorted(data, key=str.lower)
        self.text_value = ', '.join(data)
        self.count = len(data)


class IndicoStrictKeywordsField(Field):
    widget = DropdownWidget(allow_additions=False, multiple=True)

    def __init__(self, *args, **kwargs):
        self.serialized_choices = kwargs.pop('choices', [])
        super().__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)
        self.data = sorted(json.loads(self.data))

    def _value(self, for_react=False):
        return [{'id': d, 'name': d} for d in self.data] if for_react else self.data


class IndicoTagListField(HiddenFieldList):
    widget = JinjaWidget('forms/tag_list_widget.html', single_kwargs=True)


class IndicoMultipleTagSelectField(SelectMultipleField):
    widget = JinjaWidget('forms/multiple_tag_select_widget.html', single_kwargs=True, single_line=True)


class IndicoLinkListField(JSONField):
    widget = JinjaWidget('forms/link_list_widget.html', single_kwargs=True, single_line=True)

    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)
        self.data = [link for link in self.data if link.get('title') or link.get('url')]
        if len(self.data) == 1:
            if self.data[0]['url']:
                self.data[0]['title'] = ''
            else:
                self.data = []

    def pre_validate(self, form):
        if not all(x.get('url') for x in self.data):
            raise ValidationError(_('URL is required'))
        if len(self.data) > 1 and not all(x.get('title') for x in self.data):
            raise ValidationError(_('Titles are required when more than one link is specified'))


class IndicoParticipantVisibilityField(JSONField):
    widget = JinjaWidget('forms/participant_visibility_widget.html', single_kwargs=True, single_line=True)
    choices = [(mode.name, mode.title) for mode in PublishRegistrationsMode]
    max_visibility_period = 521
