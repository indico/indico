# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from operator import attrgetter

from flask import request, session
from sqlalchemy.orm import joinedload
from wtforms.ext.sqlalchemy.fields import QuerySelectField

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
from indico.modules.events.util import serialize_person_link
from indico.modules.users.models.users import User
from indico.util.decorators import classproperty
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.fields import JSONField
from indico.web.forms.widgets import JinjaWidget, SelectizeWidget


def _serialize_user(user):
    return {
        'id': user.id,
        'name': user.name
    }


def _get_users_in_roles(data):
    user_ids = {user_id
                for user_roles in data.viewvalues()
                for users in user_roles.viewvalues()
                for user_id in users}
    if not user_ids:
        return []
    return db.session.query(User.id, User).filter(User.id.in_(user_ids)).all()


def _get_users(ids):
    if not ids:
        return set()
    return set(User.find(User.id.in_(ids), ~User.is_deleted))


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
                'options': list(c.get_available_values(event=self.event).viewitems()),
                'compatibleWith': c.compatible_with,
                'required': c.required
            } for c in self.accepted_condition_types
        }

    def pre_validate(self, form):
        super(EmailRuleListField, self).pre_validate(form)
        if not all(self.data):
            raise ValueError(_('Rules may not be empty'))
        if any('*' in crit for rule in self.data for crit in rule.itervalues()):
            # '*' (any) rules should never be included in the JSON, and having
            # such an entry would result in the rule never passing.
            raise ValueError('Unexpected "*" criterion')

    def _value(self):
        return super(EmailRuleListField, self)._value() if self.data else '[]'


class AbstractPersonLinkListField(PersonLinkListFieldBase):
    """A field to configure a list of abstract persons."""

    person_link_cls = AbstractPersonLink
    linked_object_attr = 'abstract'
    default_sort_alpha = False
    create_untrusted_persons = True
    widget = JinjaWidget('events/contributions/forms/contribution_person_link_widget.html', allow_empty_email=True)

    def __init__(self, *args, **kwargs):
        self.author_types = AuthorType.serialize()
        self.allow_authors = True
        self.allow_submitters = False
        self.show_empty_coauthors = kwargs.pop('show_empty_coauthors', True)
        self.default_author_type = kwargs.pop('default_author_type', AuthorType.none)
        self.default_is_submitter = False
        self.default_is_speaker = False
        self.require_primary_author = True
        self.sort_by_last_name = True
        self.disable_user_search = kwargs.pop('disable_user_search', False)
        super(AbstractPersonLinkListField, self).__init__(*args, **kwargs)

    def _convert_data(self, data):
        return list({self._get_person_link(x) for x in data})

    @no_autoflush
    def _get_person_link(self, data):
        extra_data = {'author_type': data.pop('authorType', self.default_author_type),
                      'is_speaker': data.pop('isSpeaker', self.default_is_speaker)}
        return super(AbstractPersonLinkListField, self)._get_person_link(data, extra_data)

    def _serialize_person_link(self, principal, extra_data=None):
        extra_data = extra_data or {}
        data = dict(extra_data, **serialize_person_link(principal))
        data['isSpeaker'] = principal.is_speaker
        data['authorType'] = principal.author_type.value
        return data

    def pre_validate(self, form):
        super(AbstractPersonLinkListField, self).pre_validate(form)
        for person_link in self.data:
            if not self.allow_authors and person_link.author_type != AuthorType.none:
                if not self.object_data or person_link not in self.object_data:
                    person_link.author_type = AuthorType.none
            if person_link.author_type == AuthorType.none and not person_link.is_speaker:
                raise ValueError(_("{} has no role").format(person_link.full_name))


class AbstractField(QuerySelectField):
    """A selectize-based field to select an abstract from an event."""

    widget = SelectizeWidget(allow_by_id=True, search_field='title', label_field='full_title', preload=True,
                             search_method='POST', inline_js=True)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('allow_blank', True)
        kwargs.setdefault('render_kw', {}).setdefault('placeholder', _('Enter abstract title or #id'))
        kwargs['query_factory'] = self._get_query
        kwargs['get_label'] = lambda a: '#{}: {}'.format(a.friendly_id, a.title)
        self.ajax_endpoint = kwargs.pop('ajax_endpoint')
        self.excluded_abstract_ids = set()
        super(AbstractField, self).__init__(*args, **kwargs)

    @classmethod
    def _serialize_abstract(cls, abstract):
        return {'id': abstract.id, 'friendly_id': abstract.friendly_id, 'title': abstract.title,
                'full_title': '#{}: {}'.format(abstract.friendly_id, abstract.title)}

    def _get_query(self):
        query = Abstract.query.with_parent(self.event).options(joinedload('submitter').lazyload('*'))
        excluded = set(map(int, request.form.getlist('excluded_abstract_id')))
        if excluded:
            query = query.filter(Abstract.id.notin_(excluded))
        return query.order_by(Abstract.friendly_id)

    def _get_object_list(self):
        return [(key, abstract)
                for key, abstract in super(AbstractField, self)._get_object_list()
                if abstract.can_access(session.user)]

    def _value(self):
        return self._serialize_abstract(self.data) if self.data else None

    def pre_validate(self, form):
        super(AbstractField, self).pre_validate(form)
        if self.data is not None and self.data.id in self.excluded_abstract_ids:
            raise ValueError(_('This abstract cannot be selected.'))

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
        return super(TrackRoleField, self)._value() if self.data else '[]'
