# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico; if not, see <http://www.gnu.org/licenses/>.


def retrieve_principals(iterable):
    """Retrieves principal objects from `(type, id)` tuples.

    Valid principal types are 'Avatar' and 'Group'
    """
    from MaKaC.user import AvatarHolder, GroupHolder

    ah = AvatarHolder()
    gh = GroupHolder()
    principals = []
    for type_, id_ in iterable:
        if type_ == 'Avatar':
            principal = ah.getById(id_)
        else:
            principal = gh.getById(id_)
        if principal:
            principals.append(principal)
    return principals
