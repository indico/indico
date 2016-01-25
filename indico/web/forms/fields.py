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

import json
import uuid
from collections import OrderedDict
from datetime import time, timedelta
from operator import attrgetter

from markupsafe import escape
from wtforms.ext.dateutil.fields import DateTimeField
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from wtforms.fields.simple import HiddenField, TextAreaField, PasswordField
from wtforms.widgets.core import CheckboxInput, Select
from wtforms.fields.core import RadioField, SelectMultipleField, SelectFieldBase, Field
from wtforms.validators import StopValidation

from indico.core.db.sqlalchemy.colors import ColorTuple
from indico.modules.groups import GroupProxy
from indico.modules.groups.util import serialize_group
from indico.modules.users import User
from indico.modules.users.util import serialize_user
from indico.util.date_time import localize_as_utc
from indico.util.i18n import _
from indico.util.user import retrieve_principals, principal_from_fossil
from indico.util.string import is_valid_mail, sanitize_email
from indico.web.forms.widgets import JinjaWidget, PasswordWidget
from indico.web.forms.validators import DateTimeRange, LinkedDateTime
from MaKaC.common.timezoneUtils import DisplayTZ


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
    widget = JinjaWidget('forms/checkbox_group_widget.html', single_kwargs=True)
    option_widget = CheckboxInput()


class IndicoRadioField(RadioField):
    widget = JinjaWidget('forms/radio_buttons_widget.html', single_kwargs=True)

    def __init__(self, *args, **kwargs):
        self.option_orientation = kwargs.pop('orientation', 'vertical')
        super(IndicoRadioField, self).__init__(*args, **kwargs)


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

    def _validate_item(self, line):
        pass

    def pre_validate(self, form):
        for line in self.data:
            self._validate_item(line)

    def _value(self):
        return u'\n'.join(self.data) if self.data else u''


class EmailListField(TextListField):
    def process_formdata(self, valuelist):
        super(EmailListField, self).process_formdata(valuelist)
        self.data = map(sanitize_email, self.data)

    def _validate_item(self, line):
        if not is_valid_mail(line, False):
            raise ValueError(_(u'Invalid email address: {}').format(escape(line)))


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


class PrincipalListField(HiddenField):
    """A field that lets you select a list Indico user/group ("principal")

    :param groups: If groups should be selectable.
    :param allow_external: If "search users with no indico account"
                           should be available.  Selecting such a user
                           will automatically create a pending user once
                           the form is submitted, even if other fields
                           in the form fail to validate!
    :param serializable: If True, the field will use a principal tuple
                         such as ``('User', user_id)`` instead of the
                         actual :class:`.User` or :class:`.GroupProxy`
                         object.
    """

    widget = JinjaWidget('forms/principal_list_widget.html')

    def __init__(self, *args, **kwargs):
        self.groups = kwargs.pop('groups', False)
        # Whether it is allowed to search for external users with no indico account
        self.allow_external = kwargs.pop('allow_external', False)
        # if we want serializable objects (usually for json) or the real thing (User/GroupProxy)
        self.serializable = kwargs.pop('serializable', True)
        super(PrincipalListField, self).__init__(*args, **kwargs)

    def _convert_principal(self, principal):
        principal = principal_from_fossil(principal, allow_pending=self.allow_external, legacy=False)
        return principal.as_principal if self.serializable else principal

    def process_formdata(self, valuelist):
        if valuelist:
            data = map(self._convert_principal, json.loads(valuelist[0]))
            self.data = data if self.serializable else set(data)

    def pre_validate(self, form):
        if self.groups:
            return
        if not self.serializable and any(isinstance(p, GroupProxy) for p in self._get_data()):
            raise ValueError(u'You cannot select groups')
        elif self.serializable and any(p[0] == 'Group' for p in self._get_data()):
            raise ValueError(u'You cannot select groups')

    def _value(self):
        if self.serializable:
            data = retrieve_principals(self._get_data(), legacy=False)
        else:
            data = self._get_data()
        data.sort(key=lambda x: x.name.lower())
        return [serialize_user(x) if isinstance(x, User) else serialize_group(x) for x in data]

    def _get_data(self):
        return sorted(self.data) if self.data else []


class PrincipalField(PrincipalListField):
    """A field that lets you select an Indico user/group ("principal")"""

    widget = JinjaWidget('forms/principal_widget.html', single_line=True)

    def _get_data(self):
        return [] if self.data is None else [self.data]

    def process_formdata(self, valuelist):
        if valuelist:
            data = map(self._convert_principal, json.loads(valuelist[0]))
            self.data = None if not data else data[0]


class MultiStringField(HiddenField):
    """A field with multiple input text fields.

    :param field: A tuple ``(fieldname, title)`` where the title is used in the
                  placeholder.
    :param uuid_field: If set, each item will have a UUID assigned and
                       stored in the field specified here.
    :param unique: Whether the values should be unique.
    :param sortable: Whether items should be sortable.
    """
    widget = JinjaWidget('forms/multiple_text_input_widget.html')
    widget.single_line = True

    def __init__(self, *args, **kwargs):
        (self.field_name, self.field_caption) = kwargs.pop('field')
        self.sortable = kwargs.pop('sortable', False)
        self.unique = kwargs.pop('unique', False)
        self.uuid_field = kwargs.pop('uuid_field', None)
        super(MultiStringField, self).__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = json.loads(valuelist[0])
            if self.uuid_field:
                for item in self.data:
                    if self.uuid_field not in item:
                        item[self.uuid_field] = unicode(uuid.uuid4())

    def pre_validate(self, form):
        if not all(isinstance(item, dict) for item in self.data):
            raise ValueError(u'Invalid data. Expected list of dicts.')
        if self.unique:
            unique_values = {item[self.field_name] for item in self.data}
            if len(unique_values) != len(self.data):
                raise ValueError(u'Items must be unique')
        if self.uuid_field:
            unique_uuids = {uuid.UUID(item[self.uuid_field], version=4) for item in self.data}
            if len(unique_uuids) != len(self.data):
                raise ValueError(u'UUIDs must be unique')
        if not all(item[self.field_name].strip() for item in self.data):
            raise ValueError(u'Empty items are not allowed')

    def _value(self):
        return self.data or []


class MultipleItemsField(HiddenField):
    """A field with multiple items consisting of multiple string values.

    :param fields: A list of ``(fieldname, title)`` tuples
    :param uuid_field: If set, each item will have a UUID assigned and
                       stored in the field specified here.  The name
                       specified here may not be in `fields`.
    :param unique_field: The name of a field in `fields` that needs
                         to be unique.
    :param sortable: Whether items should be sortable.
    """
    widget = JinjaWidget('forms/multiple_items_widget.html')

    def __init__(self, *args, **kwargs):
        self.fields = kwargs.pop('fields')
        self.uuid_field = kwargs.pop('uuid_field', None)
        self.unique_field = kwargs.pop('unique_field', None)
        self.sortable = kwargs.pop('sortable', False)
        if self.uuid_field:
            assert self.uuid_field != self.unique_field
            assert self.uuid_field not in self.fields
        self.field_names = dict(self.fields)
        super(MultipleItemsField, self).__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = json.loads(valuelist[0])
            if self.uuid_field:
                for item in self.data:
                    if self.uuid_field not in item:
                        item[self.uuid_field] = unicode(uuid.uuid4())

    def pre_validate(self, form):
        unique_used = set()
        uuid_used = set()
        for item in self.data:
            if not isinstance(item, dict):
                raise ValueError(u'Invalid item type: {}'.format(type(item).__name__))
            item_keys = set(item)
            if self.uuid_field:
                item_keys.discard(self.uuid_field)
            if item_keys != {x[0] for x in self.fields}:
                raise ValueError(u'Invalid item (bad keys): {}'.format(escape(u', '.join(item.viewkeys()))))
            if self.unique_field:
                if item[self.unique_field] in unique_used:
                    raise ValueError(u'{} must be unique'.format(self.field_names[self.unique_field]))
                unique_used.add(item[self.unique_field])
            if self.uuid_field:
                if item[self.uuid_field] in uuid_used:
                    raise ValueError(u'UUID must be unique')
                # raises ValueError if uuid is invalid
                uuid.UUID(item[self.uuid_field], version=4)
                uuid_used.add(item[self.uuid_field])

    def _value(self):
        return self.data or []


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


class TimeDeltaField(Field):
    """A field that lets the user select a simple timedelta.

    It does not support mixing multiple units, but it is smart enough
    to switch to a different unit to represent a timedelta that could
    not be represented otherwise.

    :param units: The available units. Must be a tuple containing any
                  any of 'seconds', 'minutes', 'hours' and 'days'.
                  If not specified, ``('hours', 'days')`` is assumed.
    """
    widget = JinjaWidget('forms/timedelta_widget.html', single_line=True, single_kwargs=True)
    unit_names = {
        'seconds': _(u'Seconds'),
        'minutes': _(u'Minutes'),
        'hours': _(u'Hours'),
        'days': _(u'Days')
    }
    magnitudes = OrderedDict([
        ('days', 86400),
        ('hours', 3600),
        ('minutes', 60),
        ('seconds', 1)
    ])

    def __init__(self, *args, **kwargs):
        self.units = kwargs.pop('units', ('hours', 'days'))
        super(TimeDeltaField, self).__init__(*args, **kwargs)

    @property
    def best_unit(self):
        """Returns the largest unit that covers the current timedelta"""
        if self.data is None:
            return None
        seconds = int(self.data.total_seconds())
        for unit, magnitude in self.magnitudes.iteritems():
            if not seconds % magnitude:
                return unit
        return 'seconds'

    @property
    def choices(self):
        best_unit = self.best_unit
        choices = [(unit, self.unit_names[unit]) for unit in self.units]
        # Add whatever unit is necessary to represent the currenet value if we have one
        if best_unit and best_unit not in self.units:
            choices.append((best_unit, u'({})'.format(self.unit_names[best_unit])))
        return choices

    def process_formdata(self, valuelist):
        if valuelist and len(valuelist) == 2:
            value = int(valuelist[0])
            unit = valuelist[1]
            if unit not in self.magnitudes:
                raise ValueError(u'Invalid unit')
            self.data = timedelta(seconds=self.magnitudes[unit] * value)

    def pre_validate(self, form):
        if self.best_unit in self.units:
            return
        if self.object_data is None:
            raise ValueError(_(u'Please choose a valid unit.'))
        if self.object_data != self.data:
            raise ValueError(_(u'Please choose a different unit or keep the previous value.'))

    def _value(self):
        if self.data is None:
            return u'', u''
        else:
            return int(self.data.total_seconds()) // self.magnitudes[self.best_unit], self.best_unit


class IndicoDateTimeField(DateTimeField):
    """"Friendly datetime field that handles timezones and validations."""

    widget = JinjaWidget('forms/datetime_widget.html', single_line=True)

    def __init__(self, *args, **kwargs):
        self._timezone = kwargs.pop('timezone', None)
        self.default_time = kwargs.pop('default_time', time(0, 0))
        self.date_missing = False
        self.time_missing = False
        super(IndicoDateTimeField, self).__init__(*args, parse_kwargs={'dayfirst': True}, **kwargs)

    def pre_validate(self, form):
        if self.date_missing:
            raise StopValidation(_("Date must be specified"))
        if self.time_missing:
            raise StopValidation(_("Time must be specified"))
        if self.object_data:
            # Normalize datetime resolution of passed data
            self.object_data = self.object_data.replace(second=0, microsecond=0)

    def process_formdata(self, valuelist):
        if any(valuelist):
            if not valuelist[0]:
                self.date_missing = True
            if not valuelist[1]:
                self.time_missing = True
        if valuelist:
            valuelist = [' '.join(valuelist).strip()]
        super(IndicoDateTimeField, self).process_formdata(valuelist)
        if self.data and not self.data.tzinfo:
            self.data = localize_as_utc(self.data, self.timezone)

    @property
    def earliest_dt(self):
        if self.flags.datetime_range:
            for validator in self.validators:
                if isinstance(validator, DateTimeRange):
                    return validator.get_earliest(self.get_form(), self)

    @property
    def latest_dt(self):
        if self.flags.datetime_range:
            for validator in self.validators:
                if isinstance(validator, DateTimeRange):
                    return validator.get_latest(self.get_form(), self)

    @property
    def linked_datetime_validator(self):
        if self.flags.linked_datetime:
            for validator in self.validators:
                if isinstance(validator, LinkedDateTime):
                    return validator

    @property
    def linked_field(self):
        validator = self.linked_datetime_validator
        return validator.linked_field if validator else None

    @property
    def timezone(self):
        if self._timezone:
            return self._timezone
        form = self.get_form()
        if form and hasattr(self, 'timezone'):
            return form.timezone
        session_tz = DisplayTZ().getDisplayTZ()
        return session_tz


class IndicoStaticTextField(Field):
    """Returns an html element with text taken from this field's value"""
    widget = JinjaWidget('forms/static_text_widget.html')

    def __init__(self, *args, **kwargs):
        self.text_value = kwargs.pop('text')
        super(IndicoStaticTextField, self).__init__(*args, **kwargs)

    def _value(self):
        return self.text_value


class IndicoPalettePickerField(JSONField):
    """Field allowing user to pick a color from a set of predefined values"""

    widget = JinjaWidget('forms/palette_picker_widget.html')

    def __init__(self, *args, **kwargs):
        self.color_list = kwargs.pop('color_list')
        super(IndicoPalettePickerField, self).__init__(*args, **kwargs)

    def pre_validate(self, form):
        if self.data not in self.color_list:
            raise ValueError(_('Invalid colors selected'))

    def process_formdata(self, valuelist):
        super(IndicoPalettePickerField, self).process_formdata(valuelist)
        self.data = ColorTuple(self.data['text'], self.data['background'])

    def populate_obj(self, obj, name):
        setattr(obj, name, self.data)

    def _value(self):
        return self.data._asdict()
