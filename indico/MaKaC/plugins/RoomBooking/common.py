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
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

# legacy imports
from MaKaC.plugins.base import PluginsHolder
from MaKaC.accessControl import AdminList
from MaKaC import user as user_mod


def getRoomBookingOption(opt):
    return PluginsHolder().getPluginType('RoomBooking').getOption(opt).getValue()


def rb_check_user_access(user):
    """
    Check if user should have access to RB module in general
    """

    authorized = PluginsHolder().getPluginType("RoomBooking").getOption("AuthorisedUsersGroups").getValue()

    if AdminList.getInstance().isAdmin(user):
        # user is admin
        return True
    elif len(authorized) == 0:
        # the authorization list is empty (it's disabled)
        return True
    else:
        # there is something in the authorization list
        for entity in authorized:
            if isinstance(entity, user_mod.Group) and entity.containsUser(user) or \
                    isinstance(entity, user_mod.Avatar) and entity == user:
                return True

    return False
