# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from __future__ import absolute_import, unicode_literals

import json
import uuid

from markupsafe import escape
from wtforms import HiddenField

from indico.web.forms.fields.util import is_preprocessed_formdata
from indico.web.forms.widgets import JinjaWidget


class MultiStringField(HiddenField):
    """A field with multiple input text fields.

    :param field: A tuple ``(fieldname, title)`` where the title is used in the
                  placeholder.
    :param uuid_field: If set, each item will have a UUID assigned and
                       stored in the field specified here.
    :param flat: If True, the field returns a list of string values instead
                 of dicts.  Cannot be combined with `uuid_field`.
    :param unique: Whether the values should be unique.
    :param sortable: Whether items should be sortable.
    """

    widget = JinjaWidget('forms/multiple_text_input_widget.html', single_line=True)

    def __init__(self, *args, **kwargs):
        self.field_name, self.field_caption = kwargs.pop('field')
        self.sortable = kwargs.pop('sortable', False)
        self.unique = kwargs.pop('unique', False)
        self.flat = kwargs.pop('flat', False)
        self.uuid_field = kwargs.pop('uuid_field', None)
        if self.flat and self.uuid_field:
            raise ValueError('`uuid_field` and `flat` are mutually exclusive')
        super(MultiStringField, self).__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        if is_preprocessed_formdata(valuelist):
            self.data = valuelist[0]
        elif valuelist:
            self.data = json.loads(valuelist[0])
            if self.uuid_field:
                for item in self.data:
                    if self.uuid_field not in item:
                        item[self.uuid_field] = unicode(uuid.uuid4())

    def pre_validate(self, form):
        try:
            if not all(isinstance(item, dict) for item in self.data):
                raise ValueError('Invalid data. Expected list of dicts.')
            if self.unique:
                unique_values = {item[self.field_name] for item in self.data}
                if len(unique_values) != len(self.data):
                    raise ValueError('Items must be unique')
            if self.uuid_field:
                unique_uuids = {uuid.UUID(item[self.uuid_field], version=4) for item in self.data}
                if len(unique_uuids) != len(self.data):
                    raise ValueError('UUIDs must be unique')
            if not all(item[self.field_name].strip() for item in self.data):
                raise ValueError('Empty items are not allowed')
        finally:
            if self.flat:
                self.data = [x[self.field_name] for x in self.data]

    def _value(self):
        if not self.data:
            return []
        elif self.flat:
            return [{self.field_name: x} for x in self.data]
        else:
            return self.data


class MultipleItemsField(HiddenField):
    """A field with multiple items consisting of multiple string values.

    :param fields: A list of dicts with the following arguments:
                   'id': the unique ID of the field
                   'caption': the title of the column and the placeholder
                   'type': 'text|number|select', the type of the field
                   'coerce': callable to convert the value to a python type.
                             the type must be comvertible back to a string,
                             so usually you just want something like `int`
                             or `float` here.
                   In case the type is 'select', the property 'choices' of the
                   `MultipleItemsField` or the 'choices' kwarg needs to be a dict
                   where the key is the 'id' of the select field and the value is
                   another dict mapping the option's id to it caption.
    :param uuid_field: If set, each item will have a UUID assigned and
                       stored in the field specified here.  The name
                       specified here may not be in `fields`.
    :param uuid_field_opaque: If set, the `uuid_field` is considered opaque,
                              i.e. it is never touched by this field.  This
                              is useful when you subclass the field and use
                              e.g. actual database IDs instead of UUIDs.
    :param unique_field: The name of a field in `fields` that needs
                         to be unique.
    :param sortable: Whether items should be sortable.
    """

    widget = JinjaWidget('forms/multiple_items_widget.html')

    def __init__(self, *args, **kwargs):
        self.fields = getattr(self, 'fields', None) or kwargs.pop('fields')
        self.uuid_field = kwargs.pop('uuid_field', None)
        self.uuid_field_opaque = kwargs.pop('uuid_field_opaque', False)
        self.unique_field = kwargs.pop('unique_field', None)
        self.sortable = kwargs.pop('sortable', False)
        self.choices = getattr(self, 'choices', kwargs.pop('choices', {}))
        self.serialized_data = {}
        if self.uuid_field:
            assert self.uuid_field != self.unique_field
            assert self.uuid_field not in self.fields
        self.field_names = {item['id']: item['caption'] for item in self.fields}
        super(MultipleItemsField, self).__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        if is_preprocessed_formdata(valuelist):
            self.data = valuelist[0]
        if valuelist:
            self.data = json.loads(valuelist[0])
            # Preserve dict data, because the self.data can be modified by a subclass
            self.serialized_data = json.loads(valuelist[0])
            if self.uuid_field and not self.uuid_field_opaque:
                for item in self.data:
                    if self.uuid_field not in item:
                        item[self.uuid_field] = unicode(uuid.uuid4())

    def pre_validate(self, form):
        unique_used = set()
        uuid_used = set()
        coercions = {f['id']: f['coerce'] for f in self.fields if f.get('coerce') is not None}
        for i, item in enumerate(self.serialized_data):
            if not isinstance(item, dict):
                raise ValueError('Invalid item type: {}'.format(type(item).__name__))
            item_keys = set(item)
            if self.uuid_field:
                item_keys.discard(self.uuid_field)
            if item_keys != {x['id'] for x in self.fields}:
                raise ValueError('Invalid item (bad keys): {}'.format(escape(', '.join(item.viewkeys()))))
            if self.unique_field:
                if item[self.unique_field] in unique_used:
                    raise ValueError('{} must be unique'.format(self.field_names[self.unique_field]))
                unique_used.add(item[self.unique_field])
            if self.uuid_field and not self.uuid_field_opaque:
                if item[self.uuid_field] in uuid_used:
                    raise ValueError('UUID must be unique')
                # raises ValueError if uuid is invalid
                uuid.UUID(item[self.uuid_field], version=4)
                uuid_used.add(item[self.uuid_field])
            for key, fn in coercions.viewitems():
                try:
                    self.data[i][key] = fn(self.data[i][key])
                except ValueError:
                    raise ValueError(u"Invalid value for field '{}': {}".format(self.field_names[key],
                                                                                escape(item[key])))

    def _value(self):
        return self.data or []

    @property
    def _field_spec(self):
        # Field data for the widget; skip non-json-serializable data
        return [{k: v for k, v in field.iteritems() if k != 'coerce'}
                for field in self.fields]


class OverrideMultipleItemsField(HiddenField):
    """A field similar to `MultipleItemsField` which allows the user to override some values.

    :param fields: a list of ``(fieldname, title)`` tuples. Should match
                   the fields of the corresponding `MultipleItemsField`.
    :param field_data: the data from the corresponding `MultipleItemsField`.
    :param unique_field: the name of the field which is unique among all rows
    :param edit_fields: a set containing the field names which can be edited

    If you decide to use this field, please consider adding support
    for `uuid_field` here!
    """

    widget = JinjaWidget('forms/override_multiple_items_widget.html')

    def __init__(self, *args, **kwargs):
        self.fields = kwargs.pop('fields')
        self.field_data = kwargs.pop('field_data', None)  # usually set after creating the form instance
        self.unique_field = kwargs.pop('unique_field')
        self.edit_fields = set(kwargs.pop('edit_fields'))
        super(OverrideMultipleItemsField, self).__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        if is_preprocessed_formdata(valuelist):
            self.data = valuelist[0]
        elif valuelist:
            self.data = json.loads(valuelist[0])

    def pre_validate(self, form):
        valid_keys = {x[self.unique_field] for x in self.field_data}
        for key, values in self.data.items():
            if key not in valid_keys:
                # e.g. a row removed from field_data that had a value before
                del self.data[key]
                continue
            if set(values.viewkeys()) > self.edit_fields:
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
