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

from functools import wraps

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import EmailPrincipal
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


def principal_from_fossil(fossil, allow_pending=False, allow_groups=True, allow_missing_groups=False,
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

            data = {k: '' if v is None else v for k, v in data.items()}
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
        return user
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
        return group
    elif allow_groups and type_ in {'LDAPGroupWrapper', 'MultipassGroup'}:
        provider = fossil['provider']
        group = GroupProxy(id_, provider)
        if group.group is None and not allow_missing_groups:
            raise ValueError('Multipass group does not exist: {}:{}'.format(provider, id_))
        return group
    else:
        raise ValueError('Unexpected fossil type: {}'.format(type_))


def unify_user_args(fn):
    """Decorator that unifies new/legacy user arguments.

    Any argument of the decorated function that contains a
    :class:`AvatarUserWrapper` will be converted to a :class:`User`.
    """
    def _convert(arg):
        from indico.modules.users.legacy import AvatarUserWrapper
        return arg.user if isinstance(arg, AvatarUserWrapper) else arg

    @wraps(fn)
    def wrapper(*args, **kwargs):
        args = map(_convert, args)
        kwargs = {k: _convert(v) for k, v in kwargs.iteritems()}
        return fn(*args, **kwargs)

    return wrapper
