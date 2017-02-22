# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

import json

from sqlalchemy import inspect
from wtforms import SelectField

from indico.core import signals
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.core.errors import UserValueError
from indico.modules.events.layout import theme_settings
from indico.modules.events.models.persons import EventPersonLink, EventPerson, PersonLinkBase
from indico.modules.events.models.references import ReferenceType
from indico.modules.events.util import serialize_person_link
from indico.modules.users import User
from indico.modules.users.models.users import UserTitle
from indico.modules.users.util import get_user_by_email
from indico.util.i18n import _
from indico.web.forms.fields import MultipleItemsField, PrincipalListField
from indico.web.forms.widgets import JinjaWidget


class ReferencesField(MultipleItemsField):
    """A field to manage external references."""

    def __init__(self, *args, **kwargs):
        self.reference_class = kwargs.pop('reference_class')
        self.fields = [{'id': 'type', 'caption': _("Type"), 'type': 'select', 'required': True},
                       {'id': 'value', 'caption': _("Value"), 'type': 'text', 'required': True}]
        self.choices = {'type': {unicode(r.id): r.name for r in ReferenceType.find_all()}}
        super(ReferencesField, self).__init__(*args, uuid_field='id', uuid_field_opaque=True, **kwargs)

    def process_formdata(self, valuelist):
        super(ReferencesField, self).process_formdata(valuelist)
        if valuelist:
            existing = {x.id: x for x in self.object_data or ()}
            data = []
            for entry in self.data:
                ref = existing[int(entry['id'])] if entry.get('id') is not None else None
                type_id = int(entry['type'])
                value = entry['value']
                if ref is None or (ref.reference_type_id, ref.value) != (type_id, value):
                    # Create a new ref if it's a new entry or something changed.
                    # We never UPDATE entries as modifying persistent objects
                    # here would result in them being committed even in case
                    # form validation fails somewhere else...
                    ref = self.reference_class()
                ref.reference_type_id = type_id
                ref.value = value
                data.append(ref)
            self.data = data

    def pre_validate(self, form):
        super(ReferencesField, self).pre_validate(form)
        for reference in self.serialized_data:
            if reference['type'] not in self.choices['type']:
                raise ValueError(u'Invalid type choice: {}'.format(reference['type']))

    def _value(self):
        if not self.data:
            return []
        else:
            return [{'id': r.id, 'type': unicode(r.reference_type_id), 'value': r.value} for r in self.data]


class EventPersonListField(PrincipalListField):
    """A field that lets you select a list Indico user and EventPersons

    Requires its form to have an event set.
    """

    #: Whether new event persons created by the field should be
    #: marked as untrusted
    create_untrusted_persons = False

    def __init__(self, *args, **kwargs):
        self.event_person_conversions = {}
        super(EventPersonListField, self).__init__(*args, groups=False, allow_external=True, **kwargs)

    @property
    def event(self):
        return getattr(self.get_form(), 'event', None)

    def _convert_data(self, data):
        return map(self._get_event_person, data)

    def _create_event_person(self, data):
        title = next((x.value for x in UserTitle if data.get('title') == x.title), None)
        person = EventPerson(event_new=self.event, email=data.get('email', '').lower(), _title=title,
                             first_name=data.get('firstName'), last_name=data['familyName'],
                             affiliation=data.get('affiliation'), address=data.get('address'),
                             phone=data.get('phone'), is_untrusted=self.create_untrusted_persons)
        # Keep the original data to cancel the conversion if the person is not persisted to the db
        self.event_person_conversions[person] = data
        return person

    def _get_event_person_for_user(self, user):
        person = EventPerson.for_user(user, self.event, is_untrusted=self.create_untrusted_persons)
        # Keep a reference to the user to cancel the conversion if the person is not persisted to the db
        self.event_person_conversions[person] = user
        return person

    def _get_event_person(self, data):
        person_type = data.get('_type')
        if person_type is None:
            if data.get('email'):
                email = data['email'].lower()
                user = User.find_first(~User.is_deleted, User.all_emails.contains(email))
                if user:
                    return self._get_event_person_for_user(user)
                elif self.event:
                    person = self.event.persons.filter_by(email=email).first()
                    if person:
                        return person
            # We have no way to identify an existing event person with the provided information
            return self._create_event_person(data)
        elif person_type == 'Avatar':
            return self._get_event_person_for_user(self._convert_principal(data))
        elif person_type == 'EventPerson':
            return self.event.persons.filter_by(id=data['id']).one()
        elif person_type == 'PersonLink':
            return self.event.persons.filter_by(id=data['personId']).one()
        else:
            raise ValueError(_("Unknown person type '{}'").format(person_type))

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


class PersonLinkListFieldBase(EventPersonListField):
    #: class that inherits from `PersonLinkBase`
    person_link_cls = None
    #: name of the attribute on the form containing the linked object
    linked_object_attr = None
    #: If set to `True`, will be sorted alphabetically by default
    default_sort_alpha = True

    widget = None

    def __init__(self, *args, **kwargs):
        super(PersonLinkListFieldBase, self).__init__(*args, **kwargs)
        self.object = getattr(kwargs['_form'], self.linked_object_attr, None)

    @no_autoflush
    def _get_person_link(self, data, extra_data=None):
        extra_data = extra_data or {}
        person = self._get_event_person(data)
        person_data = {'title': next((x.value for x in UserTitle if data.get('title') == x.title), UserTitle.none),
                       'first_name': data.get('firstName', ''), 'last_name': data['familyName'],
                       'affiliation': data.get('affiliation', ''), 'address': data.get('address', ''),
                       'phone': data.get('phone', ''), 'display_order': data['displayOrder']}
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
                person_link.person.user = get_user_by_email(email)
                signals.event.person_updated.send(person_link.person)
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

    def _value(self):
        return [self._serialize_person_link(person_link) for person_link in self.data] if self.data else []


class EventPersonLinkListField(PersonLinkListFieldBase):
    """A field to manage event's chairpersons"""

    person_link_cls = EventPersonLink
    linked_object_attr = 'event'
    widget = JinjaWidget('events/forms/event_person_link_widget.html')

    def __init__(self, *args, **kwargs):
        self.allow_submitters = True
        self.default_is_submitter = kwargs.pop('default_is_submitter', True)
        super(EventPersonLinkListField, self).__init__(*args, **kwargs)

    def _convert_data(self, data):
        return {self._get_person_link(x): x.pop('isSubmitter', self.default_is_submitter) for x in data}

    def _serialize_person_link(self, principal, extra_data=None):
        extra_data = extra_data or {}
        data = dict(extra_data, **serialize_person_link(principal))
        data['isSubmitter'] = principal.is_submitter
        return data

    def pre_validate(self, form):
        super(PersonLinkListFieldBase, self).pre_validate(form)
        persons = set()
        for person_link in self.data:
            if person_link.person in persons:
                raise ValueError(_("Person with email '{}' is duplicated").format(person_link.person.email))
            persons.add(person_link.person)


class IndicoThemeSelectField(SelectField):
    def __init__(self, *args, **kwargs):
        allow_default = kwargs.pop('allow_default', False)
        event_type = kwargs.pop('event_type').legacy_name
        super(IndicoThemeSelectField, self).__init__(*args, **kwargs)
        self.choices = sorted([(tid, theme['title'])
                               for tid, theme in theme_settings.get_themes_for(event_type).viewitems()
                               if not theme.get('is_xml')],
                              key=lambda x: x[1].lower())
        if allow_default:
            self.choices.insert(0, ('', _('Category default')))
        self.default = '' if allow_default else theme_settings.defaults[event_type]


class ReviewQuestionsField(MultipleItemsField):
    def __init__(self, *args, **kwargs):
        self.extra_fields = kwargs.pop('extra_fields', [])
        self.fields = [{'id': 'text', 'caption': _("Question"), 'type': 'text', 'required': True}] + self.extra_fields
        self.question_model = kwargs.pop('question_model')
        super(ReviewQuestionsField, self).__init__(*args, uuid_field='id', uuid_field_opaque=True, sortable=True,
                                                   **kwargs)

    def process_formdata(self, valuelist):
        super(ReviewQuestionsField, self).process_formdata(valuelist)
        if valuelist:
            existing = {x.id: x for x in self.object_data or ()}
            data = []
            for pos, entry in enumerate(self.data, 1):
                question = (existing.pop(int(entry['id'])) if entry.get('id') is not None else self.question_model())
                question.text = entry['text']
                question.position = pos
                for extra_field in self.extra_fields:
                    setattr(question, extra_field['id'], entry[extra_field['id']])
                data.append(question)
            for question in existing.itervalues():
                if question.ratings:
                    # keep it around and soft-delete if it has been used; otherwise we just skip it
                    # which will delete it once it's gone from the relationship (when populating the
                    # Event from the form's data)
                    question.is_deleted = True
                    data.append(question)
            self.data = data

    def _value(self):
        if not self.data:
            return []
        else:
            rv = []
            for question in self.data:
                data = {'id': question.id, 'text': question.text}
                for extra_field in self.extra_fields:
                    data[extra_field['id']] = getattr(question, extra_field['id'])
                rv.append(data)
            return rv
