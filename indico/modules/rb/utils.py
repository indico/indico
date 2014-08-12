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

from indico.util.caching import memoize_request
from indico.util.user import retrieve_principals, principals_merge_users


@memoize_request
def rb_check_user_access(user):
    """Checks if the user has access to the room booking system"""
    from indico.modules.rb import settings

    if user.isRBAdmin():
        return True
    principals = retrieve_principals(settings.get('authorized_principals', []))
    if not principals:  # everyone has access
        return True
    return any(principal.containsUser(user) for principal in principals)


def rb_merge_users(new_id, old_id):
    """Updates RB data after an Avatar merge

    :param new_id: Target user
    :param old_id: Source user (being deleted in the merge)
    """
    from indico.modules.rb import settings
    from indico.modules.rb.models.blocking_principals import BlockingPrincipal
    from indico.modules.rb.models.blockings import Blocking
    from indico.modules.rb.models.reservations import Reservation
    from indico.modules.rb.models.rooms import Room

    BlockingPrincipal.find(entity_type='Avatar', entity_id=old_id).update({'entity_id': new_id})
    Blocking.find(created_by_id=old_id).update({'created_by_id': new_id})
    Reservation.find(created_by_id=old_id).update({'created_by_id': new_id})
    Reservation.find(booked_for_id=old_id).update({'booked_for_id': new_id})
    Room.find(owner_id=old_id).update({'owner_id': new_id})
    for key in ('authorized_principals', 'admin_principals'):
        principals = settings.get(key, [])
        principals = principals_merge_users(principals, new_id, old_id)
        settings.set(key, principals)
