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

from warnings import warn

from flask_multipass import MultipassException
from werkzeug.utils import cached_property

from indico.core.auth import multipass
from indico.core.db import db
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.modules.auth import Identity
from indico.modules.groups.models.groups import LocalGroup
from indico.util.caching import memoize_request
from indico.util.string import return_ascii
from indico.legacy.common.cache import GenericCache


class GroupProxy(object):
    """Provides a generic interface for both local and multipass groups.

    Creating an instance of this class actually creates either a
    ``LocalGroupProxy`` or a ``MultipassGroupProxy``, but they expose
    the same API.

    :param name_or_id: The name of a multipass group or ID of a
                       local group
    :param provider: The provider of a multipass group
    """

    # Useful when dealing with both users and groups in the same code
    is_group = True
    is_network = False
    is_single_person = False
    principal_order = 2

    def __new__(cls, name_or_id, provider=None, _group=None):
        """Creates the correct GroupProxy for the group type"""
        if provider is None or provider == 'indico':
            obj = object.__new__(_LocalGroupProxy)
            obj.id = int(name_or_id)
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

    def __contains__(self, user):
        if not user:
            return False
        return self.has_member(user)

    @cached_property
    def group(self):
        """The underlying group object"""
        raise NotImplementedError

    @cached_property
    def as_principal(self):
        """The serializable principal identifier of this group"""
        raise NotImplementedError

    @cached_property
    def as_legacy_group(self):
        """The legacy-style group wrapper"""
        # TODO: remove once groups are gone from ZODB
        raise NotImplementedError

    @property
    def as_legacy(self):
        return self.as_legacy_group

    def has_member(self, user):
        """Checks if the user is a member of the group.

        This can also be accessed using the ``in`` operator.
        """
        raise NotImplementedError

    def get_members(self):
        """Gets the list of users who are members of the group"""
        raise NotImplementedError

    @classmethod
    def get_named_default_group(cls, name):
        """Gets the group with the matching name from the default group provider.

        If there is no default group provider, local groups will be
        used and `name` is the group's ID.

        This method should only be used for legacy code or code that
        gets the group name from an external source which does not
        contain a provider identifier.
        """
        group_provider = multipass.default_group_provider
        return cls(name, group_provider.name if group_provider else None)

    @classmethod
    def search(cls, name, exact=False, providers=None):
        """Searches for groups

        :param name: The group name to search for.
        :param exact: If only exact matches should be found (much faster)
        :param providers: ``None`` to search in all providers and
                          local groups. May be a set specifying
                          providers to search in. For local groups, the
                          ``'indico'`` provider name may be used.
        """
        name = name.strip()
        if not name:
            return []
        if exact:
            criterion = db.func.lower(LocalGroup.name) == name.lower()
        else:
            criterion = db.func.lower(LocalGroup.name).contains(name.lower())
        result = set()
        if providers is None or 'indico' in providers:
            result |= {g.proxy for g in LocalGroup.find(criterion)}
        result |= {GroupProxy(g.name, g.provider.name, _group=g)
                   for g in multipass.search_groups(name, providers=providers, exact=exact)}
        return sorted(result, key=lambda x: x.name.lower())


class _LocalGroupProxy(GroupProxy):
    is_local = True
    supports_member_list = True
    provider = None
    principal_type = PrincipalType.local_group

    @property
    def locator(self):
        return {'provider': 'indico', 'group_id': self.id}

    @property
    def name(self):
        return self.group.name if self.group else '({})'.format(self.id)

    @cached_property
    def group(self):
        """The underlying :class:`.LocalGroup`"""
        return LocalGroup.get(self.id)

    @cached_property
    def as_principal(self):
        return 'Group', (None, self.id)

    @cached_property
    def as_legacy_group(self):
        from indico.modules.groups.legacy import LocalGroupWrapper
        return LocalGroupWrapper(self.id)

    def has_member(self, user):
        return user and self.group in user.local_groups

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
        if not self.group:
            return '<LocalGroupProxy({} [missing])>'.format(self.id)
        else:
            return '<LocalGroupProxy({}, {})>'.format(self.id, self.group.name)


class _MultipassGroupProxy(GroupProxy):
    is_local = False
    principal_type = PrincipalType.multipass_group

    @property
    def locator(self):
        return {'provider': self.provider, 'group_id': self.name}

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

    @cached_property
    def as_principal(self):
        return 'Group', (self.provider, self.name)

    @cached_property
    def as_legacy_group(self):
        from indico.modules.groups.legacy import LDAPGroupWrapper
        return LDAPGroupWrapper(self.name)

    @property
    def provider_title(self):
        return multipass.identity_providers[self.provider].title

    def has_member(self, user):
        if not user:
            return False
        cache = GenericCache('group-membership')
        key = '{}:{}:{}'.format(self.provider, self.name, user.id)
        rv = cache.get(key)
        if rv is not None:
            return rv
        elif self.group is None:
            warn('Tried to check if {} is in invalid group {}'.format(user, self))
            rv = False
        else:
            rv = any(x[1] in self.group for x in user.iter_identifiers(check_providers=True, providers={self.provider}))
        cache.set(key, rv, 1800)
        return rv

    @memoize_request
    def get_members(self):
        from indico.modules.users.models.users import User
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
