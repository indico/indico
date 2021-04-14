# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from warnings import warn

from flask_multipass import MultipassException
from werkzeug.utils import cached_property

from indico.core.auth import multipass
from indico.core.cache import make_scoped_cache
from indico.core.config import config
from indico.core.db import db
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.modules.auth import Identity
from indico.modules.groups.models.groups import LocalGroup
from indico.util.caching import memoize_request


group_membership_cache = make_scoped_cache('group-membership')


class GroupProxy:
    """Provide a generic interface for both local and multipass groups.

    Creating an instance of this class actually creates either a
    ``LocalGroupProxy`` or a ``MultipassGroupProxy``, but they expose
    the same API.

    :param name_or_id: The name of a multipass group or ID of a
                       local group
    :param provider: The provider of a multipass group
    """

    principal_order = 3

    def __new__(cls, name_or_id, provider=None, _group=None):
        """Create the correct GroupProxy for the group type."""
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
        """The underlying group object."""
        raise NotImplementedError

    @cached_property
    def as_principal(self):
        """The serializable principal identifier of this group."""
        raise NotImplementedError

    @property
    def identifier(self):
        provider, id_or_name = self.as_principal[1]
        return 'Group:{}:{}'.format(provider or '', id_or_name)

    def has_member(self, user):
        """Check if the user is a member of the group.

        This can also be accessed using the ``in`` operator.
        """
        raise NotImplementedError

    def get_members(self):
        """Get the list of users who are members of the group."""
        raise NotImplementedError

    @classmethod
    def search(cls, name, exact=False, providers=None):
        """Search for groups.

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
        if (providers is None or 'indico' in providers) and config.LOCAL_GROUPS:
            result |= {g.proxy for g in LocalGroup.query.filter(criterion)}
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
        return self.group.name if self.group else f'({self.id})'

    @cached_property
    def group(self):
        """The underlying :class:`.LocalGroup`"""
        if not config.LOCAL_GROUPS:
            # pretend local groups do not exist if they are disabled
            # this way they'll be rejected in acl fields
            return None
        return LocalGroup.get(self.id)

    @cached_property
    def as_principal(self):
        return 'Group', (None, self.id)

    def has_member(self, user):
        if not config.LOCAL_GROUPS:
            return False
        return user and self.group in user.local_groups

    def get_members(self):
        return set(self.group.members)

    def __eq__(self, other):
        if not isinstance(other, _LocalGroupProxy):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        if not self.group:
            return f'<LocalGroupProxy({self.id} [missing])>'
        else:
            return f'<LocalGroupProxy({self.id}, {self.group.name})>'


class _MultipassGroupProxy(GroupProxy):
    is_local = False
    principal_type = PrincipalType.multipass_group

    @property
    def locator(self):
        return {'provider': self.provider, 'group_id': self.name}

    @property
    def supports_member_list(self):
        try:
            return multipass.identity_providers[self.provider].group_class.supports_member_list
        except KeyError:
            return False

    @cached_property
    def group(self):
        """The underlying :class:`~flask_multipass.Group`."""
        try:
            return multipass.get_group(self.provider, self.name)
        except MultipassException as e:
            warn(f'Could not retrieve group {self.provider}:{self.name}: {e}')
            return None

    @cached_property
    def as_principal(self):
        return 'Group', (self.provider, self.name)

    @property
    def provider_title(self):
        try:
            return multipass.identity_providers[self.provider].title
        except KeyError:
            return self.provider.title()

    def has_member(self, user):
        if not user:
            return False
        key = f'{self.provider}:{self.name}:{user.id}'
        rv = group_membership_cache.get(key)
        if rv is not None:
            return rv
        elif self.group is None:
            warn(f'Tried to check if {user} is in invalid group {self}')
            rv = False
        else:
            rv = any(x[1] in self.group for x in user.iter_identifiers(check_providers=True, providers={self.provider}))
        group_membership_cache.set(key, rv, timeout=1800)
        return rv

    @memoize_request
    def get_members(self):
        from indico.modules.users.models.users import User
        if self.group is None:
            warn(f'Tried to get members for invalid group {self}')
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
                User.all_emails.in_(list(emails)),
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

    def __repr__(self):
        return f'<MultipassGroupProxy({self.provider}, {self.name})>'
