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

from indico.core.auth import multipass
from indico.modules.groups import GroupProxy
from indico.util.fossilize import Fossilizable, fossilizes
from indico.util.string import to_unicode, return_ascii, encode_utf8
from indico.legacy.fossils.user import IGroupFossil


class GroupWrapper(Fossilizable):
    """Group-like wrapper class that holds a DB-stored (or remote) group."""

    fossilizes(IGroupFossil)

    def __init__(self, group_id):
        self.id = to_unicode(group_id).encode('utf-8')

    @property
    def group(self):
        """Returns the underlying GroupProxy

        :rtype: indico.modules.groups.core.GroupProxy
        """
        raise NotImplementedError

    def getId(self):
        return self.id

    def getName(self):
        raise NotImplementedError

    def getFullName(self):
        return self.getName()

    def getEmail(self):
        return ''

    def exists(self):
        return self.group.group is not None

    def __eq__(self, other):
        if not hasattr(other, 'group') or not isinstance(other.group, GroupProxy):
            return False
        return self.group == other.group

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.group)

    @return_ascii
    def __repr__(self):
        return u'<{} {}: {}>'.format(type(self).__name__, self.id, self.group)


class LocalGroupWrapper(GroupWrapper):
    is_local = True
    groupType = 'Default'

    @property
    def group(self):
        return GroupProxy(self.id)

    @encode_utf8
    def getName(self):
        return self.group.group.name if self.exists() else self.id


class LDAPGroupWrapper(GroupWrapper):
    is_local = False
    provider_name = None
    groupType = 'LDAP'

    @property
    def provider(self):
        if self.provider_name:
            return self.provider_name
        provider = multipass.default_group_provider
        assert provider, 'No identity provider has default_group_provider enabled'
        return provider.name

    @property
    def group(self):
        return GroupProxy(self.id, self.provider)

    @encode_utf8
    def getName(self):
        return self.id
