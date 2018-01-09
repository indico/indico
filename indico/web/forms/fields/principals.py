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

from wtforms import HiddenField

from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.modules.groups import GroupProxy
from indico.modules.groups.util import serialize_group
from indico.modules.networks.models.networks import IPNetworkGroup
from indico.modules.networks.util import serialize_ip_network_group
from indico.modules.users.util import serialize_user
from indico.util.user import principal_from_fossil
from indico.web.forms.widgets import JinjaWidget


class PrincipalListField(HiddenField):
    """A field that lets you select a list Indico user/group ("principal")

    :param groups: If groups should be selectable.
    :param allow_networks: If ip networks should be selectable.
    :param allow_emails: If emails should be allowed.
    :param allow_external: If "search users with no indico account"
                           should be available.  Selecting such a user
                           will automatically create a pending user once
                           the form is submitted, even if other fields
                           in the form fail to validate!
    """

    widget = JinjaWidget('forms/principal_list_widget.html', single_kwargs=True)

    def __init__(self, *args, **kwargs):
        self.allow_emails = kwargs.pop('allow_emails', False)
        self.groups = kwargs.pop('groups', False)
        self.allow_networks = kwargs.pop('allow_networks', False)
        self.ip_networks = []
        if self.allow_networks:
            self.ip_networks = map(serialize_ip_network_group, IPNetworkGroup.query.filter_by(hidden=False))
        # Whether it is allowed to search for external users with no indico account
        self.allow_external = kwargs.pop('allow_external', False)
        # Whether the add user dialog is opened immediately when the field is displayed
        self.open_immediately = kwargs.pop('open_immediately', False)
        super(PrincipalListField, self).__init__(*args, **kwargs)

    def _convert_principal(self, principal):
        return principal_from_fossil(principal, allow_pending=self.allow_external,
                                     allow_emails=self.allow_emails, allow_networks=self.allow_networks,
                                     existing_data=self.object_data)

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = {self._convert_principal(x) for x in json.loads(valuelist[0])}

    def pre_validate(self, form):
        if not self.groups and any(isinstance(p, GroupProxy) for p in self._get_data()):
            raise ValueError('You cannot select groups')

    def _serialize_principal(self, principal):
        if principal.principal_type == PrincipalType.email:
            return principal.fossilize()
        elif principal.principal_type == PrincipalType.network:
            return serialize_ip_network_group(principal)
        elif principal.principal_type == PrincipalType.user:
            return serialize_user(principal)
        elif principal.is_group:
            return serialize_group(principal)
        else:
            raise ValueError('Invalid principal: {} ({})'.format(principal, principal.principal_type))

    def _value(self):
        from indico.modules.events.models.persons import PersonLinkBase

        def key(obj):
            if isinstance(obj, PersonLinkBase):
                return obj.name.lower()
            return obj.principal_type, obj.name.lower()

        principals = sorted(self._get_data(), key=key)
        return map(self._serialize_principal, principals)

    def _get_data(self):
        return sorted(self.data) if self.data else []


class AccessControlListField(PrincipalListField):
    widget = JinjaWidget('forms/principal_list_widget.html', single_kwargs=True, acl=True)

    def __init__(self, *args, **kwargs):
        # The text of the link that changes the protection mode of the object to protected
        self.default_text = kwargs.pop('default_text')
        super(AccessControlListField, self).__init__(*args, **kwargs)


class PrincipalField(PrincipalListField):
    """A field that lets you select an Indico user/group ("principal")"""

    widget = JinjaWidget('forms/principal_widget.html', single_line=True)

    def _get_data(self):
        return [] if self.data is None else [self.data]

    def process_formdata(self, valuelist):
        if valuelist:
            data = map(self._convert_principal, json.loads(valuelist[0]))
            self.data = None if not data else data[0]
