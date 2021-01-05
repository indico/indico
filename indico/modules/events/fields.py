# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import json

from sqlalchemy import inspect
from wtforms import RadioField, SelectField

from indico.core import signals
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.core.errors import UserValueError
from indico.modules.events.layout import theme_settings
from indico.modules.events.models.persons import EventPerson, EventPersonLink, PersonLinkBase
from indico.modules.events.models.references import ReferenceType
from indico.modules.events.persons.util import get_event_person
from indico.modules.events.util import serialize_person_link
from indico.modules.users.models.users import UserTitle
from indico.modules.users.util import get_user_by_email
from indico.util.i18n import _, orig_string
from indico.web.forms.fields import MultipleItemsField
from indico.web.forms.fields.principals import PrincipalListField
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
    """A field that lets you select a list Indico user and EventPersons.

    This requires its form to have an event set.
    """

    #: Whether new event persons created by the field should be
    #: marked as untrusted
    create_untrusted_persons = False

    def __init__(self, *args, **kwargs):
        self.event_person_conversions = {}
        super(EventPersonListField, self).__init__(*args, allow_groups=False, allow_external_users=True, **kwargs)

    @property
    def event(self):
        return getattr(self.get_form(), 'event', None)

    def _convert_data(self, data):
        raise NotImplementedError

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
        person = get_event_person(self.event, data, create_untrusted_persons=self.create_untrusted_persons,
                                  allow_external=True)
        person_data = {'title': next((x.value for x in UserTitle if data.get('title') == orig_string(x.title)),
                                     UserTitle.none),
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
            if not self.event or not self.event.persons.filter_by(email=email).first():
                person_link.person.email = email
                person_link.person.user = get_user_by_email(email)
                if inspect(person).persistent:
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
    """A field to manage event's chairpersons."""

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
        data['isSubmitter'] = self.data[principal] if self.get_form().is_submitted() else principal.is_submitter
        return data

    def pre_validate(self, form):
        super(EventPersonLinkListField, self).pre_validate(form)
        persons = set()
        for person_link in self.data:
            if person_link.person in persons:
                raise ValueError(_("Person with email '{}' is duplicated").format(person_link.person.email))
            persons.add(person_link.person)


class IndicoThemeSelectField(SelectField):
    def __init__(self, *args, **kwargs):
        allow_default = kwargs.pop('allow_default', False)
        event_type = kwargs.pop('event_type').name
        super(IndicoThemeSelectField, self).__init__(*args, **kwargs)
        self.choices = sorted([(tid, theme['title'])
                               for tid, theme in theme_settings.get_themes_for(event_type).viewitems()],
                              key=lambda x: x[1].lower())
        if allow_default:
            self.choices.insert(0, ('', _('Category default')))
        self.default = '' if allow_default else theme_settings.defaults[event_type]


class RatingReviewField(RadioField):
    widget = JinjaWidget('events/reviews/rating_widget.html', inline_js=True)

    def __init__(self, *args, **kwargs):
        self.question = kwargs.pop('question')
        self.rating_range = kwargs.pop('rating_range')
        super(RatingReviewField, self).__init__(*args, **kwargs)
