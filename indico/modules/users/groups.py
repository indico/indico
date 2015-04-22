# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from warnings import warn

from flask_multipass import MultipassException
from werkzeug.utils import cached_property

from indico.core.db import db
from indico.modules.auth import Identity, multipass
from indico.modules.users.models.groups import LocalGroup
from indico.modules.users.models.users import User
from indico.util.caching import memoize_request
from indico.util.string import return_ascii


class GroupProxy(object):
    """Provides a generic interface for both local and multipass groups.

    Creating an instance of this class actually creates either a
    ``LocalGroupProxy`` or a ``MultipassGroupProxy``, but they expose
    the same API.

    :param name_or_id: The name of a multipass group or ID of a
                       local group
    :param provider: The provider of a multipass group
    """

    def __new__(cls, name_or_id, provider=None, _group=None):
        """Creates the correct GroupProxy for the group type"""
        if provider is None:
            obj = object.__new__(_LocalGroupProxy)
            obj.id = name_or_id
        else:
            obj = object.__new__(_MultipassGroupProxy)
            obj.name = name_or_id
            obj.provider = provider
        if _group is not None:
            # Avoid the cached_property lookup
            obj.__dict__['group'] = _group
        return obj

    def __ne__(self, other):
        return not (self == other)

    def __eq__(self, other):
        raise NotImplementedError

    def __hash__(self):
        raise NotImplementedError

    @cached_property
    def group(self):
        """The underlying group object"""
        raise NotImplementedError

    def has_member(self, user):
        """Checks if the user is a member of the group"""
        raise NotImplementedError

    def get_members(self):
        """Gets the list of users who are members of the group"""
        raise NotImplementedError

    @classmethod
    def search(cls, name, exact=False):
        name = name.strip()
        if not name:
            return []
        if exact:
            criterion = db.func.lower(LocalGroup.name) == name.lower()
        else:
            criterion = db.func.lower(LocalGroup.name).contains(name.lower())
        result = {GroupProxy(g.id, _group=g) for g in LocalGroup.find(criterion)}
        result |= {GroupProxy(g.name, g.provider, _group=g) for g in multipass.search_groups(name, exact=exact)}
        return sorted(result, key=lambda x: x.group.name.lower())


class _LocalGroupProxy(GroupProxy):
    is_local = True
    supports_member_list = True

    @cached_property
    def group(self):
        """The underlying :class:`.LocalGroup`"""
        return LocalGroup.get(self.id)

    def has_member(self, user):
        return self.group in user.local_groups

    def get_members(self):
        return set(self.group.members)

    def __eq__(self, other):
        if not isinstance(other, _LocalGroupProxy):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    @return_ascii
    def __repr__(self):
        return '<LocalGroupProxy({}, {})>'.format(self.id, self.group.name)


class _MultipassGroupProxy(GroupProxy):
    is_local = False

    @property
    def supports_member_list(self):
        return multipass.identity_providers[self.provider].group_class.supports_member_list

    @cached_property
    def group(self):
        """The underlying :class:`~flask_multipass.Group`"""
        try:
            return multipass.get_group(self.provider, self.name)
        except MultipassException as e:
            warn('Could not retrieve group {}:{}: {}'.format(self.provider, self.name, e))
            return None

    def has_member(self, user):
        if self.group is None:
            warn('Tried to check if {} is in invalid group {}'.format(user, self))
            return False
        # First check the user's existing identities
        if any(x.identifier in self.group for x in user.identities if x.provider == self.provider):
            return True
        # If that didn't succeed, search providers based on the user's emails
        return any(identity_info.identifier in self.group
                   for email in user.all_emails
                   for identity_info in multipass.search_identities(providers={self.provider}, exact=True,
                                                                    email=email))

    @memoize_request
    def get_members(self):
        if self.group is None:
            warn('Tried to get members for invalid group {}'.format(self))
            return set()
        # We actually care about Users, not identities here!
        emails = set()
        identifiers = set()
        for identity_info in self.group:
            identifiers.add(identity_info.identifier)
            emails |= {x.lower() for x in identity_info.data.getlist('email') if x}
        if not identifiers and not emails:
            return set()
        return set(User.query.outerjoin(Identity).filter(
            ~User.is_deleted,
            db.or_(
                User.all_emails.contains(db.func.any(list(emails))),
                db.and_(
                    Identity.provider == self.provider,
                    Identity.identifier.in_(identifiers)
                )
            )))

    def __eq__(self, other):
        if not isinstance(other, _MultipassGroupProxy):
            return False
        return (self.name, self.provider) == (other.name, other.provider)

    def __hash__(self):
        return hash(self.name) ^ hash(self.provider)

    @return_ascii
    def __repr__(self):
        return '<MultipassGroupProxy({}, {})>'.format(self.provider, self.name)
