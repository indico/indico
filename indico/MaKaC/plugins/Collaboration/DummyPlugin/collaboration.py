# -*- coding: utf-8 -*-
##
## $Id: collaboration.py,v 1.4 2009/04/07 14:40:08 dmartinc Exp $
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
    
    _hasStart = True
    _hasStop = True
    
    _requiresServerCallForStart = True
    _requiresServerCallForStop = True
    
    _requiresClientCallForStart = True
    _requiresClientCallForStop = True
    
    _allowMultiple = False
        
    def __init__(self, id, type, conf):
        CSBookingBase.__init__(self, id, type, conf)
        self._bookingParams = {
            "username": None,
            "favouriteColor": None
        }
            
    def create(self):
        if self._bookingParams["username"] == "David":
            self._statusMessage = "Booking accepted"
            self._statusClass = "statusMessageOK"
            self._canBeStarted = True
        else:
            self._statusMessage = "Booking refused"
            self._statusClass = "statusMessageError"
            self._canBeStarted = False
            
    def start(self):
        if self._bookingParams["favouriteColor"] == "blue":
            self._permissionToStart = True
            self._canBeStarted = False
            self._canBeStopped = True
            from MaKaC.common.utils import logToApache
            logToApache("Starting booking with id " + str(self._id))
        else:
            from MaKaC.common.utils import logToApache
            logToApache("Why you don't like blue? id " + str(self._id))
            
    def modify(self):
        self.create()
                    
    def stop(self):
        self._permissionToStop = True
        self._canBeStarted = True
        self._canBeStopped = False
        from MaKaC.common.utils import logToApache
        logToApache("Stopping booking with id " + str(self._id))
                    
    def delete(self):
        from MaKaC.common.utils import logToApache
        logToApache("Deleting booking with id " + str(self._id))
        
    