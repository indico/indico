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


def retrieve_principals(iterable):
    """
    Retrieves principal objects from `(type, id)` tuples.

    Valid principal types are 'Avatar' and 'Group'
    """

    return filter(None, map(retrieve_principal, iterable))


def retrieve_principal(principal):
    """
    Retrieves principal object from a `(type, id)` tuple.

    Valid principal types are 'Avatar' and 'Group'
    """
    from MaKaC.user import AvatarHolder, GroupHolder

    ah = AvatarHolder()
    gh = GroupHolder()

    type_, id_ = principal
    return ah.getById(id_) if type_ == 'Avatar' else gh.getById(id_)


def principal_to_tuple(principal):
    """
    Translates an Avatar or Group to a tuple of the form (<class_name>, <id>)
    """
    return principal.__class__.__name__, principal.id


def principals_merge_users(iterable, new_id, old_id):
    """Creates a new principal list with one user being replaced with another one

    :param iterable: Iterable containing `(type, id)` tuples
    :param new_id: Target user
    :param old_id: Source user (being deleted in the merge)
    """
    principals = []
    for type_, id_ in iterable:
        if type_ == 'Avatar' and int(id_) == int(old_id):
            id_ = new_id
        principals.append((type_, id_))
    return principals
