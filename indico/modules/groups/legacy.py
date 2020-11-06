# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.


from zope.interface.declarations import implementer

from indico.legacy.fossils.user import IGroupFossil
from indico.modules.groups import GroupProxy
from indico.util.fossilize import Fossilizable
from indico.util.string import encode_utf8, to_unicode


@implementer(IGroupFossil)
class GroupWrapper(Fossilizable):
    """Group-like wrapper class that holds a DB-stored (or remote) group."""

    def __init__(self, group_id):
        self.id = to_unicode(group_id).encode('utf-8')

    @property
    def group(self):
        """Return the underlying GroupProxy.

        :rtype: indico.modules.groups.core.GroupProxy
        """
        raise NotImplementedError

    def getId(self):
        return self.id

    def getName(self):
        raise NotImplementedError

    def getEmail(self):
        return ''

    def __repr__(self):
        return '<{} {}: {}>'.format(type(self).__name__, self.id, self.group)


class LocalGroupWrapper(GroupWrapper):
    is_local = True
    groupType = 'Default'

    @encode_utf8
    def getName(self):
        return GroupProxy(self.id).name


class LDAPGroupWrapper(GroupWrapper):
    is_local = False
    groupType = 'LDAP'

    def __init__(self, group_id, provider_name):
        super().__init__(group_id)
        self.provider_name = provider_name

    @property
    def provider(self):
        return self.provider_name

    @encode_utf8
    def getName(self):
        return self.id
