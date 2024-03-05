# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from operator import attrgetter

from flask import request, session
from sqlalchemy.orm import joinedload
from wtforms import ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField

from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.core.permissions import get_permissions_info
from indico.modules.categories.util import serialize_category_role
from indico.modules.events.abstracts.models.abstracts import Abstract
from indico.modules.events.abstracts.models.persons import AbstractPersonLink
from indico.modules.events.abstracts.notifications import ContributionTypeCondition, StateCondition, TrackCondition
from indico.modules.events.contributions.models.persons import AuthorType
from indico.modules.events.fields import PersonLinkListFieldBase
from indico.modules.events.roles.util import serialize_event_role
from indico.modules.events.tracks.models.tracks import Track
from indico.modules.users.models.users import User
from indico.util.decorators import classproperty
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.fields import JSONField
from indico.web.forms.widgets import DropdownWidget, JinjaWidget


def _serialize_user(user):
    return {
        'id': user.id,
        'name': user.name
    }


def _get_users_in_roles(data):
    user_ids = {user_id
                for user_roles in data.values()
                for users in user_roles.values()
                for user_id in users}
    if not user_ids:
        return []
    return db.session.query(User.id, User).filter(User.id.in_(user_ids)).all()


def _get_users(ids):
    if not ids:
        return set()
    return set(User.query.filter(User.id.in_(ids), ~User.is_deleted))


class EmailRuleListField(JSONField):
    """A field that stores a list of e-mail template rules."""

    CAN_POPULATE = True
    widget = JinjaWidget('events/abstracts/forms/rule_list_widget.html')
    accepted_condition_types = (StateCondition, TrackCondition, ContributionTypeCondition)

    @classproperty
    @classmethod
    def condition_class_map(cls):
        return {r.name: r for r in cls.accepted_condition_types}

    @property
    def condition_choices(self):
        return {
            c.name: {
                'title': c.description,
                'labelText': c.label_text,
                'options': list(c.get_available_values(event=self.event).items()),
                'compatibleWith': c.compatible_with,
                'required': c.required
            } for c in self.accepted_condition_types
        }

    def pre_validate(self, form):
        super().pre_validate(form)
        if not all(self.data):
            raise ValidationError(_('Rules may not be empty'))
        if any('*' in crit for rule in self.data for crit in rule.values()):
            # '*' (any) rules should never be included in the JSON, and having
            # such an entry would result in the rule never passing.
            raise ValidationError('Unexpected "*" criterion')

    def _value(self):
        return super()._value() if self.data else '[]'


class AbstractPersonLinkListField(PersonLinkListFieldBase):
    """A field to configure a list of abstract persons."""

    person_link_cls = AbstractPersonLink
    linked_object_attr = 'abstract'
    default_sort_alpha = False
    create_untrusted_persons = True
    widget = JinjaWidget('forms/person_link_widget.html', allow_empty_email=True)

    @property
    def roles(self):
        roles = [
            {'name': 'primary', 'label': _('Author'), 'plural': _('Authors'), 'section': True, 'default': True},
            {'name': 'secondary', 'label': _('Co-author'), 'plural': _('Co-authors'), 'section': True},
        ]
        if self.allow_speakers:
            roles.append({'name': 'speaker', 'label': _('Speaker'), 'icon': 'microphone'})
        return roles

    def __init__(self, *args, **kwargs):
        self.allow_speakers = kwargs.pop('allow_speakers', True)
        self.require_primary_author = kwargs.pop('require_primary_author', True)
        self.require_speaker = kwargs.pop('require_speaker', False)
        self.sort_by_last_name = True
        self.empty_message = _('There are no authors')
        super().__init__(*args, **kwargs)

    @no_autoflush
    def _get_person_link(self, data):
        person_link = super()._get_person_link(data)
        roles = data.get('roles', [])
        person_link.is_speaker = 'speaker' in roles
        person_link.author_type = next((AuthorType.get(a) for a in roles if AuthorType.get(a)), AuthorType.none)
        return person_link

    def _serialize_person_link(self, principal):
        from indico.modules.events.persons.schemas import PersonLinkSchema
        data = PersonLinkSchema().dump(principal)
        data['roles'] = []
        if principal.is_speaker:
            data['roles'].append('speaker')
        data['roles'].append(principal.author_type.name)
        return data

    def pre_validate(self, form):
        super().pre_validate(form)
        for person_link in self.data:
            if person_link.author_type == AuthorType.none and not person_link.is_speaker:
                raise ValidationError(_('{} has no role').format(person_link.full_name))
        if (self.require_primary_author and
                not any(person_link.author_type == AuthorType.primary for person_link in self.data)):
            raise ValidationError(_('You must add at least one author'))
        if self.require_speaker and not any(person_link.is_speaker for person_link in self.data):
            raise ValidationError(_('You must add at least one speaker'))


class AbstractField(QuerySelectField):
    """A field with dynamic fetching to select an abstract from an event."""

    widget = DropdownWidget(allow_by_id=True, search_field='title', label_field='full_title', preload=True,
                            search_method='POST', inline_js=True)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('allow_blank', True)
        kwargs.setdefault('render_kw', {}).setdefault('placeholder', _('Enter abstract title or #id'))
        kwargs['query_factory'] = self._get_query
        kwargs['get_label'] = lambda a: f'#{a.friendly_id}: {a.title}'
        self.ajax_endpoint = kwargs.pop('ajax_endpoint')
        self.excluded_abstract_ids = set()
        super().__init__(*args, **kwargs)

    @classmethod
    def _serialize_abstract(cls, abstract):
        return {'id': abstract.id, 'friendly_id': abstract.friendly_id, 'title': abstract.title,
                'full_title': f'#{abstract.friendly_id}: {abstract.title}'}

    def _get_query(self):
        query = Abstract.query.with_parent(self.event).options(joinedload('submitter').lazyload('*'))
        excluded = set(map(int, request.form.getlist('excluded_abstract_id')))
        if excluded:
            query = query.filter(Abstract.id.notin_(excluded))
        return query.order_by(Abstract.friendly_id)

    def _get_object_list(self):
        return [(key, abstract)
                for key, abstract in super()._get_object_list()
                if abstract.can_access(session.user)]

    def _value(self, for_react=False):
        if not self.data:
            return None
        return [self._serialize_abstract(self.data)] if for_react else self.data.id

    def pre_validate(self, form):
        super().pre_validate(form)
        if self.data is not None and self.data.id in self.excluded_abstract_ids:
            raise ValidationError(_('This abstract cannot be selected.'))

    @property
    def event(self):
        # This cannot be accessed in __init__ since `get_form` is set
        # afterwards (when the field gets bound to its form) so we
        # need to access it through a property instead.
        return self.get_form().event

    @property
    def search_url(self):
        return url_for(self.ajax_endpoint, self.event)

    @property
    def search_payload(self):
        return {'excluded_abstract_id': list(self.excluded_abstract_ids)}


class TrackRoleField(JSONField):
    """A field to assign track roles to principals."""

    CAN_POPULATE = True
    widget = JinjaWidget('events/abstracts/forms/track_role_widget.html')

    @property
    def permissions_info(self):
        permissions, tree, default = get_permissions_info(Track)
        return {'permissions': permissions, 'tree': tree['_full_access']['children'], 'default': default}

    @property
    def event_roles(self):
        return [serialize_event_role(role, legacy=False) for role in sorted(self.event.roles, key=attrgetter('code'))]

    @property
    def category_roles(self):
        from indico.modules.categories.models.roles import CategoryRole
        category_roles = CategoryRole.get_category_roles(self.event.category)
        return [serialize_category_role(role) for role in category_roles]

    def _value(self):
        return super()._value() if self.data else '[]'
