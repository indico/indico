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

from functools import wraps

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import EmailPrincipal
from indico.util.decorators import smart_decorator

from indico.legacy.common.cache import GenericCache


def iter_acl(acl):
    """Iterates over an ACL in the most efficient order.

    This first yields users/emails, then ip networks, then local
    groups, and eventually multipass groups as a remote group check
    is much more expensive than checking if two users are the same
    (``==``), if an ip is in a network (just some math) or if a user
    is in a local group (SQL query).

    :param acl: any iterable containing users/groups or objects which
                contain users/groups in a `principal` attribute
    """
    return sorted(acl, key=lambda x: (getattr(x, 'principal', x).principal_order,
                                      not getattr(getattr(x, 'principal', x), 'is_local', None)))


def principal_is_only_for_user(acl, user, principal):
    """Checks if the given principal is the only one for a user.

    :param acl: A list of principals.
    :param user: The user to check for
    :param principal: The principal to check for.
    """
    # if the principal doesn't apply for the user, it can't be the last one for him
    if user not in principal:
        return False
    return not any(user in entry.principal for entry in iter_acl(acl) if entry.principal != principal)


def retrieve_principals(iterable, allow_groups=True, legacy=True):
    """Retrieves principal objects from ``(type, info)`` tuples.

    See :func:`retrieve_principal` for details.
    """

    return filter(None, [retrieve_principal(x, allow_groups=allow_groups, legacy=legacy) for x in iterable])


def retrieve_principal(principal, allow_groups=True, legacy=True):
    """Retrieves principal object from a `(type, id)` tuple.

    Valid principal types are 'Avatar', 'User' and 'Group'.

    :param principal: The principal (a tuple/list)
    :param allow_groups: If group principals are allowed
    :param legacy: If legacy wrappers or new objects should be returned.
    """
    from indico.modules.groups import GroupProxy
    from indico.modules.groups.legacy import LocalGroupWrapper, LDAPGroupWrapper
    from indico.modules.users import User

    type_, id_ = principal
    if type_ in {'Avatar', 'User'}:
        user = User.get(int(id_))
        if not user:
            return None
        return user.as_avatar if legacy else user
    elif type_ == 'Group' and allow_groups:
        if isinstance(id_, (int, basestring)):  # legacy group
            group = LocalGroupWrapper(id_) if unicode(id_).isdigit() else LDAPGroupWrapper(id_)
            return group if legacy else group.group
        else:  # new group
            provider, name_or_id = id_
            group = GroupProxy(name_or_id, provider)
            return group.as_legacy_group if legacy else group
    else:
        raise ValueError('Unexpected type: {}'.format(type_))


def principal_from_fossil(fossil, allow_pending=False, allow_groups=True, legacy=True, allow_missing_groups=False,
                          allow_emails=False, allow_networks=False, existing_data=None):
    from indico.modules.networks.models.networks import IPNetworkGroup
    from indico.modules.groups import GroupProxy
    from indico.modules.users import User

    if existing_data is None:
        existing_data = set()

    type_ = fossil['_type']
    id_ = fossil['id']
    if type_ == 'Avatar':
        if isinstance(id_, int) or id_.isdigit():
            # regular user
            user = User.get(int(id_))
        elif allow_pending:
            data = GenericCache('pending_identities').get(id_)
            if not data:
                raise ValueError("Cannot find user '{}' in cache".format(id_))

            data = {k: '' if v is None else v for (k, v) in data.items()}
            email = data['email'].lower()

            # check if there is not already a (pending) user with that e-mail
            # we need to check for non-pending users too since the search may
            # show a user from external results even though the email belongs
            # to an indico account in case some of the search criteria did not
            # match the indico account
            user = User.find_first(User.all_emails.contains(email), ~User.is_deleted)
            if not user:
                user = User(first_name=data.get('first_name') or '', last_name=data.get('last_name') or '',
                            email=email,
                            address=data.get('address', ''), phone=data.get('phone', ''),
                            affiliation=data.get('affiliation', ''), is_pending=True)
                db.session.add(user)
                db.session.flush()
        else:
            raise ValueError("Id '{}' is not a number and allow_pending=False".format(id_))
        if user is None:
            raise ValueError('User does not exist: {}'.format(id_))
        return user.as_avatar if legacy else user
    elif allow_emails and type_ == 'Email':
        return EmailPrincipal(id_)
    elif allow_networks and type_ == 'IPNetworkGroup':
        group = IPNetworkGroup.get(int(id_))
        if group is None or (group.hidden and group not in existing_data):
            raise ValueError('IP network group does not exist: {}'.format(id_))
        return group
    elif allow_groups and type_ in {'LocalGroupWrapper', 'LocalGroup'}:
        group = GroupProxy(int(id_))
        if group.group is None:
            raise ValueError('Local group does not exist: {}'.format(id_))
        return group.as_legacy_group if legacy else group
    elif allow_groups and type_ in {'LDAPGroupWrapper', 'MultipassGroup'}:
        provider = fossil['provider']
        group = GroupProxy(id_, provider)
        if group.group is None and not allow_missing_groups:
            raise ValueError('Multipass group does not exist: {}:{}'.format(provider, id_))
        return group.as_legacy_group if legacy else group
    else:
        raise ValueError('Unexpected fossil type: {}'.format(type_))


@smart_decorator
def unify_user_args(fn, legacy=False):
    """Decorator that unifies new/legacy user arguments.

    Any argument of the decorated function that contains either a
    :class:`AvatarUserWrapper` or a :class:`.User` will be converted
    to the object type specified by the `legacy` argument.

    :param legacy: If True, all arguments containing users will receive
                   an :class:`AvatarUserWrapper`. Otherwise, they will
                   receive a :class:`.User`.
    """
    from indico.modules.users import User

    if legacy:
        def _convert(arg):
            return arg.as_avatar if isinstance(arg, User) else arg
    else:
        def _convert(arg):
            from indico.modules.users.legacy import AvatarUserWrapper
            return arg.user if isinstance(arg, AvatarUserWrapper) else arg

    @wraps(fn)
    def wrapper(*args, **kwargs):
        args = map(_convert, args)
        kwargs = {k: _convert(v) for k, v in kwargs.iteritems()}
        return fn(*args, **kwargs)

    return wrapper
