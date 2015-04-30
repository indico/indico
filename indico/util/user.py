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

from indico.core.db import db
from indico.modules.groups import GroupProxy
from indico.modules.users import User

from MaKaC.common.cache import GenericCache


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
    from indico.modules.groups.legacy import LocalGroupWrapper, LDAPGroupWrapper
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


def principals_merge_users(iterable, new_id, old_id):
    """Creates a new principal list with one user being replaced with another one

    :param iterable: Iterable containing `(type, id)` tuples
    :param new_id: Target user
    :param old_id: Source user (being deleted in the merge)
    """
    principals = []
    for type_, id_ in iterable:
        if type_ in {'Avatar', 'User'} and int(id_) == int(old_id):
            id_ = new_id
        principals.append((type_, id_))
    return principals


def principal_from_fossil(fossil, allow_pending=False, legacy=True):
    """Gets a GroupWrapper or AvatarUserWrapper from a fossil"""
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

            # check if there is not already a pending user with that e-mail
            user = User.find_first(email=data['email'], is_pending=True)
            if not user:
                user = User(first_name=data['first_name'], last_name=data['last_name'], email=data['email'],
                            address=data.get('address', ''), phone=data.get('phone', ''),
                            affiliation=data.get('affiliation', ''), is_pending=True)
                db.session.add(user)
                db.session.flush()
        else:
            raise ValueError("Id '{}' is not a number and allow_pending=False".format(id_))
        if user is None:
            raise ValueError('User does not exist: {}'.format(id_))
        return user.as_avatar if legacy else user
    elif type_ == 'LocalGroupWrapper':
        group = GroupProxy(int(id_))
        if group.group is None:
            raise ValueError('Local group does not exist: {}'.format(id_))
        return group.as_legacy_group if legacy else group
    elif type_ == 'LDAPGroupWrapper':
        provider = fossil['provider']
        group = GroupProxy(id_, provider)
        if group.group is None:
            raise ValueError('Multipass group does not exist: {}:{}'.format(provider, id_))
        return group.as_legacy_group if legacy else group
    else:
        raise ValueError('Unexpected fossil type: {}'.format(type_))
