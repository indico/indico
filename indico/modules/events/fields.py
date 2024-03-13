# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import json
from operator import attrgetter

from flask import session
from marshmallow import EXCLUDE
from sqlalchemy import inspect
from wtforms import RadioField, SelectField

from indico.core import signals
from indico.core.cache import make_scoped_cache
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.core.errors import UserValueError
from indico.modules.events.layout import layout_settings, theme_settings
from indico.modules.events.models.events import EventType
from indico.modules.events.models.persons import EventPersonLink
from indico.modules.events.models.references import ReferenceType
from indico.modules.events.persons import persons_settings
from indico.modules.events.persons.util import get_event_person
from indico.modules.users.models.affiliations import Affiliation
from indico.modules.users.models.users import UserTitle
from indico.modules.users.util import get_user_by_email
from indico.util.i18n import _
from indico.util.signals import values_from_signal
from indico.web.flask.util import url_for
from indico.web.forms.fields import MultipleItemsField
from indico.web.forms.fields.principals import PrincipalListField
from indico.web.forms.widgets import JinjaWidget


class ReferencesField(MultipleItemsField):
    """A field to manage external references."""

    def __init__(self, *args, **kwargs):
        self.reference_class = kwargs.pop('reference_class')
        self.fields = [{'id': 'type', 'caption': _('Type'), 'type': 'select', 'required': True},
                       {'id': 'value', 'caption': _('Value'), 'type': 'text', 'required': True}]
        self.choices = {'type': {str(r.id): r.name for r in ReferenceType.query}}
        super().__init__(*args, uuid_field='id', uuid_field_opaque=True, **kwargs)

    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)
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
        super().pre_validate(form)
        for reference in self.serialized_data:
            if reference['type'] not in self.choices['type']:
                raise ValueError('Invalid type choice: {}'.format(reference['type']))

    def _value(self):
        if not self.data:
            return []
        else:
            return [{'id': r.id, 'type': str(r.reference_type_id), 'value': r.value} for r in self.data]


class PersonLinkListFieldBase(PrincipalListField):
    #: class that inherits from `PersonLinkBase`
    person_link_cls = None
    #: name of the attribute on the form containing the linked object
    linked_object_attr = None
    #: If set to `True`, will be sorted alphabetically by default
    default_sort_alpha = True

    widget = None
    create_untrusted_persons = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, allow_groups=False, allow_external_users=True, **kwargs)
        self.object = getattr(kwargs['_form'], self.linked_object_attr, None)

    @property
    def event(self):
        # The event should be a property as it may only be available later, such as, in creation forms
        return getattr(self.get_form(), 'event', None)

    @property
    def has_predefined_affiliations(self):
        return Affiliation.query.filter(~Affiliation.is_deleted).has_rows()

    @property
    def default_search_external(self):
        if not self.event:
            return False
        return persons_settings.get(self.event, 'default_search_external')

    @property
    def can_enter_manually(self):
        if self.event is None:
            return True
        return self.event.can_manage(session.user) or not persons_settings.get(self.event, 'disallow_custom_persons')

    @property
    def name_format(self):
        from indico.modules.users.models.users import NameFormat
        name_format = layout_settings.get(self.event, 'name_format') if self.event else None
        if name_format is None and session.user:
            name_format = session.user.settings.get('name_format')
        return name_format if name_format is not None else NameFormat.first_last

    @property
    def validate_email_url(self):
        return url_for('events.check_email', self.object) if self.object else None

    @property
    def extra_params(self):
        values = values_from_signal(signals.event.person_link_field_extra_params.send(self), as_list=True)
        return {k: v for d in values for k, v in d.items()}

    @no_autoflush
    def _get_person_link(self, data):
        from indico.modules.events.persons.schemas import PersonLinkSchema
        identifier = data.get('identifier')
        affiliations_disabled = self.extra_params.get('disable_affiliations', False)
        data = PersonLinkSchema(unknown=EXCLUDE).load(data)
        if not self.can_enter_manually and not data.get('type'):
            raise UserValueError('Manually entered persons are not allowed')
        if identifier and identifier.startswith('ExternalUser:'):
            # if the data came from an external user, look up their affiliation if the names still match;
            # we do not have an affiliation ID yet since it may not exist in the local DB yet
            cache = make_scoped_cache('external-user')
            external_user_data = cache.get(identifier.removeprefix('ExternalUser:'), {})
            if not self.can_enter_manually:
                for key in ('first_name', 'last_name', 'email', 'affiliation', 'phone', 'address'):
                    data[key] = external_user_data.get(key, '')
                data['_title'] = UserTitle.none
                data['affiliation_link'] = None
            if (
                not affiliations_disabled and
                (affiliation_data := external_user_data.get('affiliation_data')) and
                data['affiliation'] == affiliation_data['name']
            ):
                data['affiliation_link'] = Affiliation.get_or_create_from_data(affiliation_data)
                data['affiliation'] = data['affiliation_link'].name
        if not self.has_predefined_affiliations or affiliations_disabled:
            data['affiliation_link'] = None
        person = get_event_person(self.event, data, create_untrusted_persons=self.create_untrusted_persons,
                                  allow_external=True)
        person_link = None
        if self.object and inspect(person).persistent:
            person_link = self.person_link_cls.query.filter_by(person=person, object=self.object).first()
        if not person_link:
            person_link = self.person_link_cls(person=person)
        if not self.can_enter_manually:
            person_link.populate_from_dict(data, keys=('display_order',))
            return person_link
        person_link.populate_from_dict(data, keys=('first_name', 'last_name', 'affiliation', 'affiliation_link',
                                                   'address', 'phone', '_title', 'display_order'))
        email = data.get('email', '').lower()
        if email != person_link.email:
            if not self.event or not self.event.persons.filter_by(email=email).first():
                person_link.person.email = email
                person_link.person.user = get_user_by_email(email)
                if inspect(person).persistent:
                    signals.event.person_updated.send(person_link.person)
            else:
                raise UserValueError(_('There is already a person with the email {email}').format(email=email))
        return person_link

    def _serialize_person_link(self, principal):
        raise NotImplementedError

    def _convert_data(self, data):
        return list({self._get_person_link(x) for x in data})

    def _value(self):
        if submitted_data := getattr(self, '_submitted_data', None):
            return submitted_data
        return [self._serialize_person_link(person_link)
                for person_link in sorted(self.data, key=attrgetter('display_order_key'))] if self.data else []

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = self._submitted_data = json.loads(valuelist[0])
            try:
                self.data = self._convert_data(self.data)
            except ValueError:
                self.data = []
                raise


class EventPersonLinkListField(PersonLinkListFieldBase):
    """A field to manage event's chairpersons."""

    person_link_cls = EventPersonLink
    linked_object_attr = 'event'
    widget = JinjaWidget('forms/person_link_widget.html')

    @property
    def roles(self):
        return [{'name': 'submitter', 'label': _('Submitter'), 'icon': 'paperclip',
                 'default': self.default_is_submitter}]

    def __init__(self, *args, **kwargs):
        self.default_is_submitter = kwargs.pop('default_is_submitter', True)
        self.empty_message = _('There are no chairpersons')
        event_type = kwargs.pop('event_type', None)
        super().__init__(*args, **kwargs)
        if not event_type and self.object:
            event_type = self.object.event.type_
        if event_type == EventType.lecture:
            self.empty_message = _('There are no speakers')

    def _convert_data(self, data):
        return {self._get_person_link(x): 'submitter' in x.get('roles', []) for x in data}

    def _serialize_person_link(self, principal):
        from indico.modules.events.persons.schemas import PersonLinkSchema
        data = PersonLinkSchema().dump(principal)
        data['roles'] = []
        if (self.get_form().is_submitted() and self.data[principal]) or (principal.event and principal.is_submitter):
            data['roles'].append('submitter')
        return data

    def pre_validate(self, form):
        super().pre_validate(form)
        persons = set()
        for person_link in self.data:
            if person_link.person in persons:
                raise ValueError(_("Person with email '{}' is duplicated").format(person_link.person.email))
            persons.add(person_link.person)


class IndicoThemeSelectField(SelectField):
    def __init__(self, *args, **kwargs):
        allow_default = kwargs.pop('allow_default', False)
        event_type = kwargs.pop('event_type').name
        super().__init__(*args, **kwargs)
        self.choices = sorted(((tid, theme['title'])
                               for tid, theme in theme_settings.get_themes_for(event_type).items()),
                              key=lambda x: x[1].lower())
        if allow_default:
            self.choices.insert(0, ('', _('Category default')))
        self.default = '' if allow_default else theme_settings.defaults[event_type]


class RatingReviewField(RadioField):
    widget = JinjaWidget('events/reviews/rating_widget.html', inline_js=True)

    def __init__(self, *args, **kwargs):
        self.question = kwargs.pop('question')
        self.rating_range = kwargs.pop('rating_range')
        super().__init__(*args, **kwargs)
