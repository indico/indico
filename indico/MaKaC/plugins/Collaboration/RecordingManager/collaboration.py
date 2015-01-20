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

from MaKaC.plugins.Collaboration.base import CSBookingBase

class CSBooking(CSBookingBase):

    _allowMultiple = False
    _hasStartDate = False
    _shouldBeIndexed = False
    _canBeNotifiedOfEventDateChanges = False
    _adminOnly = True

    def __init__(self, bookingType, conf):
        CSBookingBase.__init__(self, bookingType, conf)
        self._bookingParams = {}

    def _checkBookingParams(self):
        return False

    def _create(self):
        pass


    def _modify(self):
        pass

    def _checkStatus(self):
        pass

    def _accept(self):
        pass

    def _reject(self):
        pass

    def _delete(self):
        pass
