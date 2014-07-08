# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.

from indico.core.config import Config
from indico.core.errors import AccessError
from indico.modules.rb.controllers.utils import rb_check_user_access
from MaKaC.webinterface.rh.base import RHProtected


class RHRoomBookingProtected(RHProtected):
    def _checkSessionUser(self):
        user = self._getUser()
        if user:
            try:
                if Config.getInstance().getIsRoomBookingActive() and not rb_check_user_access(user):
                    raise AccessError()
            except KeyError:
                pass
        else:
            self._redirect(self._getLoginURL())
            self._doProcess = False


class RHRoomBookingBase(RHRoomBookingProtected):
    """Base class for room booking RHs"""
    pass
