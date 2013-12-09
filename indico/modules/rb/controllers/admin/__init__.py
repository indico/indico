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

from MaKaC.errors import MaKaCError

from indico.modules.rb.controllers import RHRoomBookingBase


class RHRoomBookingAdminBase(RHRoomBookingBase):
    """
    Adds admin authorization. All classes that implement admin
    tasks should be derived from this class.
    """
    def _checkProtection(self):
        if self._getUser() == None:
            self._checkSessionUser()
        elif not self._getUser().isRBAdmin():
            raise MaKaCError(_('You are not authorized to take this action.'))
