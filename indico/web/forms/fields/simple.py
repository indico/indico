# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals, absolute_import

import json

from markupsafe import escape
from wtforms.fields import SelectMultipleField, RadioField, HiddenField, TextAreaField, PasswordField, Field
from wtforms.widgets import CheckboxInput

from indico.util.i18n import _
from indico.util.string import sanitize_email, is_valid_mail
from indico.web.forms.fields.util import is_preprocessed_formdata
from indico.web.forms.widgets import JinjaWidget, HiddenInputs, PasswordWidget


class IndicoSelectMultipleCheckboxField(SelectMultipleField):
    widget = JinjaWidget('forms/checkbox_group_widget.html', single_kwargs=True)
    option_widget = CheckboxInput()


class IndicoRadioField(RadioField):
    widget = JinjaWidget('forms/radio_buttons_widget.html', single_kwargs=True)

    def __init__(self, *args, **kwargs):
        self.option_orientation = kwargs.pop('orientation', 'vertical')
        super(IndicoRadioField, self).__init__(*args, **kwargs)


class JSONField(HiddenField):
    #: Whether an object may be populated with the data from this field
    CAN_POPULATE = False

    def process_formdata(self, valuelist):
        if is_preprocessed_formdata(valuelist):
            self.data = valuelist[0]
        elif valuelist:
            self.data = json.loads(valuelist[0])

    def _value(self):
        return json.dumps(self.data)

    def populate_obj(self, obj, name):
        if self.CAN_POPULATE:
            super(JSONField, self).populate_obj(obj, name)


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
        super(EmailListField, self).process_formdata(valuelist)
        self.data = map(sanitize_email, self.data)

    def _validate_item(self, line):
        if not is_valid_mail(line, False):
            raise ValueError(_('Invalid email address: {}').format(escape(line)))


class IndicoPasswordField(PasswordField):
    """Password field which can show or hide the password."""

    widget = PasswordWidget()

    def __init__(self, *args, **kwargs):
        self.toggle = kwargs.pop('toggle', False)
        super(IndicoPasswordField, self).__init__(*args, **kwargs)


class IndicoStaticTextField(Field):
    """Return an html element with text taken from this field's value"""

    widget = JinjaWidget('forms/static_text_widget.html')

    def __init__(self, *args, **kwargs):
        self.text_value = kwargs.pop('text', '')
        super(IndicoStaticTextField, self).__init__(*args, **kwargs)

    def process_data(self, data):
        self.text_value = self.data = unicode(data)

    def _value(self):
        return self.text_value


class IndicoTagListField(HiddenFieldList):
    widget = JinjaWidget('forms/tag_list_widget.html', single_kwargs=True)
