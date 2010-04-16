# -*- coding: utf-8 -*-
##
## $Id: collaboration.py,v 1.12 2009/04/25 13:56:17 dmartinc Exp $
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from MaKaC.plugins.Collaboration.base import CSBookingBase

class CSBooking(CSBookingBase):

    _allowMultiple = False
    _hasStartDate = False

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
