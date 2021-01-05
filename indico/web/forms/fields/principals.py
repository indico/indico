# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import absolute_import, unicode_literals

import json
from operator import attrgetter

from wtforms import HiddenField

from indico.core.db.sqlalchemy.principals import PrincipalType, serialize_email_principal
from indico.core.permissions import get_available_permissions, get_permissions_info
from indico.modules.events import Event
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.registration.util import serialize_registration_form
from indico.modules.events.roles.util import serialize_event_role
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.groups.util import serialize_group
from indico.modules.networks.models.networks import IPNetworkGroup
from indico.modules.networks.util import serialize_ip_network_group
from indico.modules.users.util import serialize_user
from indico.util.user import principal_from_identifier
from indico.web.forms.fields import JSONField
from indico.web.forms.widgets import JinjaWidget


def serialize_principal(principal):
    from indico.modules.categories.util import serialize_category_role
    if principal.principal_type == PrincipalType.email:
        return serialize_email_principal(principal)
    elif principal.principal_type == PrincipalType.network:
        return serialize_ip_network_group(principal)
    elif principal.principal_type == PrincipalType.user:
        return serialize_user(principal)
    elif principal.principal_type == PrincipalType.event_role:
        return serialize_event_role(principal)
    elif principal.principal_type == PrincipalType.category_role:
        return serialize_category_role(principal)
    elif principal.principal_type == PrincipalType.registration_form:
        return serialize_registration_form(principal)
    elif principal.is_group:
        return serialize_group(principal)
    else:
        raise ValueError('Invalid principal: {} ({})'.format(principal, principal.principal_type))


class PrincipalListField(HiddenField):
    """A field that lets you select a list of principals.

    Principals are users or other objects represending users such as
    groups or roles that can be added to ACLs.

    :param allow_external_users: If "search users with no indico account"
                                 should be available. Selecting such a user
                                 will automatically create a pending user once
                                 the form is submitted, even if other fields
                                 in the form fail to validate!
    :param allow_groups: If groups should be selectable.
    :param allow_event_roles: If event roles should be selectable.
    :param allow_category_roles: If category roles should be selectable.
    :param allow_registration_forms: If registration form associated
                                     to an event should be selectable.
    :param allow_emails: If the field should allow bare emails. Those are not
                         selectable in the widget, but may be added to an ACL
                         through other means.
    """

    widget = JinjaWidget('forms/principal_list_widget.html', single_kwargs=True)

    def __init__(self, *args, **kwargs):
        self.allow_external_users = kwargs.pop('allow_external_users', False)
        self.allow_groups = kwargs.pop('allow_groups', False)
        self.allow_event_roles = kwargs.pop('allow_event_roles', False)
        self.allow_category_roles = kwargs.pop('allow_category_roles', False)
        self.allow_registration_forms = kwargs.pop('allow_registration_forms', False)
        self.allow_emails = kwargs.pop('allow_emails', False)
        self._event = kwargs.pop('event')(kwargs['_form']) if 'event' in kwargs else None
        super(PrincipalListField, self).__init__(*args, **kwargs)

    def _convert_principal(self, principal):
        event_id = self._event.id if self._event else None
        return principal_from_identifier(principal, event_id=event_id, allow_groups=self.allow_groups,
                                         allow_external_users=self.allow_external_users,
                                         allow_event_roles=self.allow_event_roles,
                                         allow_category_roles=self.allow_category_roles,
                                         allow_registration_forms=self.allow_registration_forms,
                                         allow_emails=self.allow_emails)

    def process_formdata(self, valuelist):
        if valuelist:
            self._submitted_data = json.loads(valuelist[0])
            self.data = {self._convert_principal(x) for x in self._submitted_data}

    def _value(self):
        try:
            return self._submitted_data
        except AttributeError:
            return [x.identifier for x in self._get_data()]

    def _get_data(self):
        return sorted(self.data) if self.data else []


class AccessControlListField(PrincipalListField):
    def __init__(self, *args, **kwargs):
        # The text of the link that changes the protection mode of the object to protected
        self.default_text = kwargs.pop('default_text')
        # Hardcoded value of the protected field for legacy compatibility
        self.protected_field_id = 'protected'
        super(AccessControlListField, self).__init__(*args, **kwargs)


class PrincipalField(HiddenField):
    """A field that lets you select a single Indico user.

    :param allow_external_users: If "search users with no indico account"
                                 should be available. Selecting such a user
                                 will automatically create a pending user once
                                 the form is submitted, even if other fields
                                 in the form fail to validate!
    """

    widget = JinjaWidget('forms/principal_widget.html', single_kwargs=True)

    def __init__(self, *args, **kwargs):
        self.allow_external_users = kwargs.pop('allow_external_users', False)
        super(PrincipalField, self).__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        if valuelist:
            self._submitted_data = valuelist[0]
            self.data = principal_from_identifier(self._submitted_data, allow_external_users=self.allow_external_users)

    def _value(self):
        try:
            return self._submitted_data
        except AttributeError:
            return self.data.identifier if self.data else ''


class PermissionsField(JSONField):
    from indico.modules.categories.models.categories import Category
    widget = JinjaWidget('forms/permissions_widget.html', single_kwargs=True, acl=True)

    type_mapping = {
        'event': Event,
        'session': Session,
        'contribution': Contribution,
        'category': Category
    }

    def __init__(self, *args, **kwargs):
        self.object_type = kwargs.pop('object_type')
        super(PermissionsField, self).__init__(*args, **kwargs)
        self.ip_networks = map(serialize_ip_network_group, IPNetworkGroup.query.filter_by(hidden=False))

    @property
    def event(self):
        return self.get_form().event

    @property
    def category(self):
        if self.object_type == 'category':
            return self.get_form().category
        return self.event.category

    @property
    def event_roles(self):
        return [serialize_event_role(role) for role in sorted(self.event.roles, key=attrgetter('code'))]

    @property
    def category_roles(self):
        from indico.modules.categories.util import serialize_category_role
        from indico.modules.categories.models.roles import CategoryRole
        category_roles = CategoryRole.get_category_roles(self.category)
        return [serialize_category_role(role, legacy=True) for role in category_roles]

    @property
    def registration_forms(self):
        if not self.event.has_feature('registration'):
            return []
        registration_forms = self.event.registration_forms
        return [serialize_registration_form(regform) for regform in registration_forms]

    @property
    def permissions_info(self):
        return get_permissions_info(PermissionsField.type_mapping[self.object_type])[0]

    @property
    def hidden_permissions_info(self):
        all_permissions = get_available_permissions(PermissionsField.type_mapping[self.object_type])
        visible_permissions = get_permissions_info(PermissionsField.type_mapping[self.object_type])[0]
        return {k: all_permissions[k].friendly_name for k in set(all_permissions) - set(visible_permissions)}

    def _value(self):
        return self.data if self.data else []
