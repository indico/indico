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

from __future__ import unicode_literals

from collections import defaultdict

from flask import request, session
from sqlalchemy.orm import joinedload
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.abstracts.models.abstracts import Abstract
from indico.modules.events.abstracts.models.persons import AbstractPersonLink
from indico.modules.events.abstracts.notifications import ContributionTypeCondition, StateCondition, TrackCondition
from indico.modules.events.contributions.models.persons import AuthorType
from indico.modules.events.fields import PersonLinkListFieldBase
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
    """A field to configure a list of abstract persons"""

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
    """A field that stores a list of e-mail template rules."""

    CAN_POPULATE = True
    widget = JinjaWidget('events/abstracts/forms/track_role_widget.html')

    @property
    def users(self):
        return {user_id: _serialize_user(user) for user_id, user in _get_users_in_roles(self.data)}

    @property
    def role_data(self):
        conveners = set()
        reviewers = set()

        # Handle global reviewers/conveners
        role_data = self.data.pop('*')
        global_conveners = _get_users(role_data['convener'])
        global_reviewers = _get_users(role_data['reviewer'])
        conveners |= global_conveners
        reviewers |= global_reviewers

        track_dict = {track.id: track for track in Track.query.with_parent(self.event).filter(Track.id.in_(self.data))}
        user_dict = dict(_get_users_in_roles(self.data))

        track_roles = {}
        # Update track-specific reviewers/conveners
        for track_id, roles in self.data.viewitems():
            track = track_dict[int(track_id)]
            track_roles[track] = defaultdict(set)
            for role_id, user_ids in roles.viewitems():
                users = {user_dict[user_id] for user_id in user_ids}
                track_roles[track][role_id] = users
                if role_id == 'convener':
                    conveners |= users
                elif role_id == 'reviewer':
                    reviewers |= users

        return {
            'track_roles': track_roles,
            'global_conveners': global_conveners,
            'global_reviewers': global_reviewers,
            'all_conveners': conveners,
            'all_reviewers': reviewers
        }

    def _value(self):
        return super(TrackRoleField, self)._value() if self.data else '[]'
