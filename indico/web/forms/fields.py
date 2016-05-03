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

from flask import render_template
from markupsafe import escape, Markup
from sqlalchemy import inspect
from sqlalchemy.orm import joinedload
from wtforms.ext.dateutil.fields import DateTimeField
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from wtforms.fields.simple import HiddenField, TextAreaField, PasswordField
from wtforms.widgets.core import CheckboxInput, Select, RadioInput
from wtforms.fields.core import RadioField, SelectMultipleField, SelectFieldBase, Field
from wtforms.validators import StopValidation

from indico.core.db import db
from indico.core.db.sqlalchemy.colors import ColorTuple
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.core.errors import UserValueError
from indico.modules.events.models.events import Event
from indico.modules.events.models.persons import EventPerson, PersonLinkBase
from indico.modules.groups import GroupProxy
from indico.modules.groups.util import serialize_group
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.rooms import Room
from indico.modules.users.models.users import User, UserTitle
from indico.modules.users.util import serialize_user
from indico.util.date_time import localize_as_utc
from indico.util.i18n import _
from indico.util.user import retrieve_principals, principal_from_fossil
from indico.util.string import is_valid_mail, sanitize_email
from indico.web.forms.validators import DateTimeRange, LinkedDateTime
from indico.web.forms.widgets import JinjaWidget, PasswordWidget, HiddenInputs, LocationWidget
from MaKaC.common.timezoneUtils import DisplayTZ


def _preprocessed_formdata(valuelist):
    if len(valuelist) != 1:
        return False
    value = valuelist[0]
    return isinstance(value, (dict, list))


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

    #: Whether an object may be populated with the data from this field
    CAN_POPULATE = False

    def process_formdata(self, valuelist):
        if _preprocessed_formdata(valuelist):
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


class IndicoLocationField(JSONField):

    CAN_POPULATE = True
    widget = LocationWidget()

    def __init__(self, *args, **kwargs):
        self.allow_location_inheritance = kwargs.pop('allow_location_inheritance', True)
        self.locations = Location.query.options(joinedload('rooms')).order_by(db.func.lower(Location.name)).all()
        super(IndicoLocationField, self).__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        super(IndicoLocationField, self).process_formdata(valuelist)
        self.data['room'] = Room.get(int(self.data['room_id'])) if self.data.get('room_id') else None
        self.data['venue'] = Location.get(int(self.data['venue_id'])) if self.data.get('venue_id') else None

    def _value(self):
        if not self.data:
            return {}
        result = {
            'address': self.data.get('address', ''),
            'inheriting': self.data.get('inheriting', False),
        }
        if self.data.get('room'):
            result['room_id'] = self.data['room'].id
            result['room_name'] = self.data['room'].full_name
            result['venue_id'] = self.data['room'].location.id
            result['venue_name'] = self.data['room'].location.name
        elif self.data.get('room_name'):
            result['room_name'] = self.data['room_name']
        if self.data.get('venue'):
            result['venue_id'] = self.data['venue'].id
            result['venue_name'] = self.data['venue'].name
        elif self.data.get('venue_name'):
            result['venue_name'] = self.data['venue_name']
        return result


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

    widget = JinjaWidget('forms/principal_list_widget.html', single_kwargs=True)

    def __init__(self, *args, **kwargs):
        self.groups = kwargs.pop('groups', False)
        # Whether it is allowed to search for external users with no indico account
        self.allow_external = kwargs.pop('allow_external', False)
        # Whether we want serializable objects (usually for json) or the real thing (User/GroupProxy)
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

    def _serialize_principal(self, principal):
        if principal.principal_type == PrincipalType.email:
            return principal.fossilize()
        elif principal.principal_type == PrincipalType.user:
            return serialize_user(principal)
        else:
            return serialize_group(principal)

    def _value(self):
        if self.serializable:
            principals = retrieve_principals(self._get_data(), legacy=False)
        else:
            principals = self._get_data()
        principals.sort(key=lambda x: x.name.lower())
        return map(self._serialize_principal, principals)

    def _get_data(self):
        return sorted(self.data) if self.data else []


class EventPersonListField(PrincipalListField):
    """"A field that lets you select a list Indico user and EventPersons

    Requires its form to have an event set.
    """

    def __init__(self, *args, **kwargs):
        self.event_person_conversions = {}
        super(EventPersonListField, self).__init__(*args, groups=False, allow_external=True, serializable=False,
                                                   **kwargs)

    @property
    def event(self):
        return self.get_form().event

    def _convert_data(self, data):
        return map(self._get_event_person, data)

    def _create_event_person(self, data):
        title = next((x.value for x in UserTitle if data.get('title') == x.title), None)
        person = EventPerson(event_new=self.event, email=data['email'].lower(), _title=title,
                             first_name=data.get('firstName'), last_name=data['familyName'],
                             affiliation=data.get('affiliation'), address=data.get('address'),
                             phone=data.get('phone'))
        # Keep the original data to cancel the conversion if the person is not persisted to the db
        self.event_person_conversions[person] = data
        return person

    def _get_event_person_for_user(self, user):
        person = EventPerson.for_user(user, self.event)
        # Keep a reference to the user to cancel the conversion if the person is not persisted to the db
        self.event_person_conversions[person] = user
        return person

    def _get_event_person(self, data):
        person_type = data.get('_type')
        if person_type is None:
            email = data['email'].lower()
            user = User.find_first(~User.is_deleted, User.all_emails.contains(email))
            if user:
                return self._get_event_person_for_user(user)
            else:
                person = self.event.persons.filter_by(email=email).first()
                return person or self._create_event_person(data)
        elif person_type == 'Avatar':
            return self._get_event_person_for_user(self._convert_principal(data))
        elif person_type == 'EventPerson':
            return self.event.persons.filter_by(id=data['id']).one()
        elif person_type == 'PersonLink':
            return self.event.persons.filter_by(id=data['personId']).one()
        else:
            raise ValueError(_("Uknown person type '{}'").format(person_type))

    def _serialize_principal(self, principal):
        from indico.modules.events.util import serialize_event_person
        if principal.id is None:
            # We created an EventPerson which has not been persisted to the
            # database. Revert the conversion.
            principal = self.event_person_conversions[principal]
            if isinstance(principal, dict):
                return principal
        if not isinstance(principal, EventPerson):
            return super(EventPersonListField, self)._serialize_principal(principal)
        return serialize_event_person(principal)

    def pre_validate(self, form):
        # Override parent behavior
        pass

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = json.loads(valuelist[0])
            try:
                self.data = self._convert_data(self.data)
            except ValueError:
                self.data = []
                raise


class PrincipalField(PrincipalListField):
    """A field that lets you select an Indico user/group ("principal")"""

    widget = JinjaWidget('forms/principal_widget.html', single_line=True)

    def _get_data(self):
        return [] if self.data is None else [self.data]

    def process_formdata(self, valuelist):
        if valuelist:
            data = map(self._convert_principal, json.loads(valuelist[0]))
            self.data = None if not data else data[0]


class EventPersonField(EventPersonListField):
    """A field to select an EventPerson or create one from an Indico user"""

    widget = JinjaWidget('forms/principal_widget.html', single_line=True)

    def _get_data(self):
        return [] if self.data is None else [self.data]


class PersonLinkListFieldBase(EventPersonListField):

    #: class that inherits from `PersonLinkBase`
    person_link_cls = None
    #: name of the attribute on the form containing the linked object
    linked_object_attr = None

    widget = None

    def __init__(self, *args, **kwargs):
        super(PersonLinkListFieldBase, self).__init__(*args, **kwargs)
        self.object = getattr(kwargs['_form'], self.linked_object_attr)

    @no_autoflush
    def _get_person_link(self, data, extra_data=None):
        extra_data = extra_data or {}
        person = self._get_event_person(data)
        person_data = {'title': next((x.value for x in UserTitle if data.get('title') == x.title), UserTitle.none),
                       'first_name': data.get('firstName', ''), 'last_name': data['familyName'],
                       'affiliation': data.get('affiliation', ''), 'address': data.get('address', ''),
                       'phone': data.get('phone', '')}
        person_data.update(extra_data)
        person_link = None
        if self.object and inspect(person).persistent:
            person_link = self.person_link_cls.find_first(person=person, object=self.object)
        if not person_link:
            person_link = self.person_link_cls(person=person)
        person_link.populate_from_dict(person_data)
        email = data.get('email', '').lower()
        if email != person_link.email:
            if not self.event.persons.filter_by(email=email).first():
                person_link.person.email = email
            else:
                raise UserValueError(_('There is already a person with the email {}').format(email))
        return person_link

    def _serialize_principal(self, principal):
        if not isinstance(principal, PersonLinkBase):
            return super(PersonLinkListFieldBase, self)._serialize_principal(principal)
        if principal.id is None:
            return super(PersonLinkListFieldBase, self)._serialize_principal(principal.person)
        else:
            return self._serialize_person_link(principal)

    def _serialize_person_link(self, principal, extra_data=None):
        raise NotImplementedError


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
        if _preprocessed_formdata(valuelist):
            self.data = valuelist[0]
        elif valuelist:
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

    :param fields: A list of dicts with the following arguments:
                   'id': the unique ID of the field
                   'caption': the title of the column and the placeholder
                   'type': 'text|select' the type of the field
                   In case the type is 'select', the property 'choices' of the
                   `MultipleItemsField` needs to be a dict where the key is the
                   'id' of the select field and the value is another dict
                   mapping the option's id to it's caption.
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
        self.choices = getattr(self, 'choices', {})
        self.serialized_data = {}
        if self.uuid_field:
            assert self.uuid_field != self.unique_field
            assert self.uuid_field not in self.fields
        self.field_names = {item['id']: item['caption'] for item in self.fields}
        super(MultipleItemsField, self).__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        if _preprocessed_formdata(valuelist):
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
        for item in self.serialized_data:
            if not isinstance(item, dict):
                raise ValueError(u'Invalid item type: {}'.format(type(item).__name__))
            item_keys = set(item)
            if self.uuid_field:
                item_keys.discard(self.uuid_field)
            if item_keys != {x['id'] for x in self.fields}:
                raise ValueError(u'Invalid item (bad keys): {}'.format(escape(u', '.join(item.viewkeys()))))
            if self.unique_field:
                if item[self.unique_field] in unique_used:
                    raise ValueError(u'{} must be unique'.format(self.field_names[self.unique_field]))
                unique_used.add(item[self.unique_field])
            if self.uuid_field and not self.uuid_field_opaque:
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
        if _preprocessed_formdata(valuelist):
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
    # XXX: do not translate, "Minutes" is ambiguous without context
    unit_names = {
        'seconds': u'Seconds',
        'minutes': u'Minutes',
        'hours': u'Hours',
        'days': u'Days'
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
        self.allow_clear = kwargs.pop('allow_clear', True)
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
        self.text_value = kwargs.pop('text', '')
        super(IndicoStaticTextField, self).__init__(*args, **kwargs)

    def process_data(self, data):
        self.text_value = self.data = unicode(data)

    def _value(self):
        return self.text_value


class IndicoPalettePickerField(JSONField):
    """Field allowing user to pick a color from a set of predefined values"""

    widget = JinjaWidget('forms/palette_picker_widget.html')
    CAN_POPULATE = True

    def __init__(self, *args, **kwargs):
        self.color_list = kwargs.pop('color_list')
        super(IndicoPalettePickerField, self).__init__(*args, **kwargs)

    def pre_validate(self, form):
        if self.data not in self.color_list:
            raise ValueError(_('Invalid colors selected'))

    def process_formdata(self, valuelist):
        super(IndicoPalettePickerField, self).process_formdata(valuelist)
        self.data = ColorTuple(self.data['text'], self.data['background'])

    def process_data(self, value):
        super(IndicoPalettePickerField, self).process_data(value)
        if self.object_data and self.object_data not in self.color_list:
            self.color_list = self.color_list + [self.object_data]

    def _value(self):
        return self.data._asdict()


class IndicoEnumRadioField(IndicoEnumSelectField):
    widget = JinjaWidget('forms/radio_buttons_widget.html', orientation='horizontal', single_kwargs=True)
    option_widget = RadioInput()


class IndicoProtectionField(IndicoEnumRadioField):
    widget = JinjaWidget('forms/protection_widget.html', single_kwargs=True)
    radio_widget = JinjaWidget('forms/radio_buttons_widget.html', orientation='horizontal', single_kwargs=True)

    def __init__(self, *args, **kwargs):
        super(IndicoProtectionField, self).__init__(*args, enum=ProtectionMode, **kwargs)

    def render_protection_message(self):
        protected_object = self.get_form().protected_object
        non_inheriting_objects = protected_object.get_non_inheriting_objects()
        parent_type = _('Event') if isinstance(protected_object.protection_parent, Event) else _('Session')
        rv = render_template('_protection_info.html', field=self, protected_object=protected_object,
                             parent_type=parent_type, non_inheriting_objects=non_inheriting_objects)
        return Markup(rv)


class IndicoTagListField(HiddenFieldList):
    widget = JinjaWidget('forms/tag_list_widget.html', single_kwargs=True)
