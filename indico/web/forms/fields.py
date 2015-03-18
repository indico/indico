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

import json
from operator import attrgetter

from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from wtforms.fields.simple import HiddenField, TextAreaField, PasswordField
from wtforms.widgets.core import CheckboxInput, PasswordInput, Select
from wtforms.fields.core import RadioField, SelectMultipleField, SelectFieldBase

from indico.util.fossilize import fossilize
from indico.util.user import retrieve_principals
from indico.util.string import is_valid_mail
from indico.util.i18n import _
from indico.web.forms.widgets import PrincipalWidget, RadioButtonsWidget, JinjaWidget, PasswordWidget


class IndicoQuerySelectMultipleField(QuerySelectMultipleField):
    """Like the parent, but with a callback that allows you to modify the list

    The callback can return a new list or yield items, and you can use it e.g. to sort the list.
    """
    def __init__(self, *args, **kwargs):
        self.modify_object_list = kwargs.pop('modify_object_list', None)
        super(IndicoQuerySelectMultipleField, self).__init__(*args, **kwargs)

    def _get_object_list(self):
        object_list = super(IndicoQuerySelectMultipleField, self)._get_object_list()
        if self.modify_object_list:
            object_list = list(self.modify_object_list(object_list))
        return object_list


class IndicoQuerySelectMultipleCheckboxField(IndicoQuerySelectMultipleField):
    option_widget = CheckboxInput()


class IndicoSelectMultipleCheckboxField(SelectMultipleField):
    widget = JinjaWidget('forms/checkbox_group_widget.html')
    option_widget = CheckboxInput()


class IndicoRadioField(RadioField):
    widget = RadioButtonsWidget()


class JSONField(HiddenField):
    def process_formdata(self, valuelist):
        if valuelist:
            self.data = json.loads(valuelist[0])

    def _value(self):
        return json.dumps(self.data)

    def populate_obj(self, obj, name):
        # We don't want to populate an object with this
        pass


class TextListField(TextAreaField):
    def process_formdata(self, valuelist):
        if valuelist:
            self.data = [line.strip() for line in valuelist[0].split('\n') if line.strip()]
        else:
            self.data = []

    def _validate_item(self, lie):
        pass

    def pre_validate(self, form):
        for line in self.data:
            self._validate_item(line)

    def _value(self):
        return u'\n'.join(self.data) if self.data else u''


class EmailListField(TextListField):
    def _validate_item(self, line):
        if not is_valid_mail(line, False):
            raise ValueError(_(u'Invalid email address: {}').format(line))


class IndicoEnumSelectField(SelectFieldBase):
    """Select field backed by a :class:`TitledEnum`"""

    widget = Select()

    def __init__(self, label=None, validators=None, enum=None, sorted=False, only=None, skip=None, none=None,
                 titles=None, **kwargs):
        super(IndicoEnumSelectField, self).__init__(label, validators, **kwargs)
        self.enum = enum
        self.sorted = sorted
        self.only = only
        self.skip = skip or set()
        self.none = none
        self.titles = titles

    def iter_choices(self):
        items = (x for x in self.enum if x not in self.skip and (self.only is None or x in self.only))
        if self.sorted:
            items = sorted(items, key=attrgetter('title'))
        if self.none is not None:
            yield ('', self.none, self.data is None)
        for item in items:
            title = item.title if self.titles is None else self.titles[item]
            yield (item.name, title, item == self.data)

    def process_formdata(self, valuelist):
        if valuelist:
            if not valuelist[0] and self.none is not None:
                self.data = None
            else:
                try:
                    self.data = self.enum[valuelist[0]]
                except KeyError:
                    raise ValueError(self.gettext('Not a valid choice'))


class IndicoPasswordField(PasswordField):
    """Password field which can show or hide the password."""
    widget = PasswordWidget()

    def __init__(self, *args, **kwargs):
        self.toggle = kwargs.pop('toggle', False)
        super(IndicoPasswordField, self).__init__(*args, **kwargs)


class PrincipalField(HiddenField):
    widget = PrincipalWidget()

    def __init__(self, *args, **kwargs):
        self.groups = kwargs.pop('groups', False)
        self.multiple = kwargs.pop('multiple', True)
        super(PrincipalField, self).__init__(*args, **kwargs)

    def _convert_principal(self, principal):
        if principal['_type'] == 'Avatar':
            return u'Avatar', principal['id']
        else:
            return u'Group', principal['id']

    def process_formdata(self, valuelist):
        if valuelist:
            data = map(self._convert_principal, json.loads(valuelist[0]))
            if self.multiple:
                self.data = data
            else:
                self.data = None if not data else data[0]

    def pre_validate(self, form):
        for principal in self._get_data():
            if not self.groups and principal[0] == 'Group':
                raise ValueError(u'You cannot select groups')

    def _value(self):
        return map(fossilize, retrieve_principals(self._get_data()))

    def _get_data(self):
        if self.multiple:
            return self.data
        else:
            return [] if self.data is None else [self.data]


class MultipleItemsField(HiddenField):
    """A field with multiple items consisting of multiple string values.

    :param fields: A list of ``(fieldname, title)`` tuples
    """
    widget = JinjaWidget('forms/multiple_items_widget.html')

    def __init__(self, *args, **kwargs):
        self.fields = kwargs.pop('fields')
        self.unique_field = kwargs.pop('unique_field', None)
        self.field_names = dict(self.fields)
        super(MultipleItemsField, self).__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = json.loads(valuelist[0])

    def pre_validate(self, form):
        unique_used = set()
        for item in self.data:
            if not isinstance(item, dict):
                raise ValueError(u'Invalid item type: {}'.format(type(item).__name__))
            elif item.viewkeys() != {x[0] for x in self.fields}:
                raise ValueError(u'Invalid item (bad keys): {}'.format(', '.join(item.viewkeys())))
            if self.unique_field:
                if item[self.unique_field] in unique_used:
                    raise ValueError(u'{} must be unique'.format(self.field_names[self.unique_field]))
                unique_used.add(item[self.unique_field])

    def _value(self):
        return self.data or []


class OverrideMultipleItemsField(HiddenField):
    """A field similar to `MultipleItemsField` which allows the user to override some values.

    :param fields: a list of ``(fieldname, title)`` tuples. Should match
                   the fields of the corresponding `MultipleItemsField`.
    :param field_data: the data from the corresponding `MultipleItemsField`.
    :param unique_field: the name of the field which is unique among all rows
    :param edit_fields: a set containing the field names which can be edited
    """
    widget = JinjaWidget('forms/override_multiple_items_widget.html')

    def __init__(self, *args, **kwargs):
        self.fields = kwargs.pop('fields')
        self.field_data = kwargs.pop('field_data', None)  # usually set after creating the form instance
        self.unique_field = kwargs.pop('unique_field')
        self.edit_fields = set(kwargs.pop('edit_fields'))
        super(OverrideMultipleItemsField, self).__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = json.loads(valuelist[0])

    def pre_validate(self, form):
        valid_keys = {x[self.unique_field] for x in self.field_data}
        for key, values in self.data.items():
            if key not in valid_keys:
                # e.g. a row removed from field_data that had a value before
                del self.data[key]
                continue
            if values.viewkeys() > self.edit_fields:
                # e.g. a field that was editable before
                self.data[key] = {k: v for k, v in values.iteritems() if k in self.edit_fields}
        # Remove anything empty
        for key, values in self.data.items():
            for field, value in values.items():
                if not value:
                    del values[field]
            if not self.data[key]:
                del self.data[key]

    def _value(self):
        return self.data or {}

    def get_overridden_value(self, row, name):
        """Utility for the widget to get the entered value for an editable field"""
        key = self.get_row_key(row)
        return self._value().get(key, {}).get(name, '')

    def get_row_key(self, row):
        """Utility for the widget to get the unique value for a row"""
        return row[self.unique_field]
