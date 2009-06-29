# -*- coding: utf-8 -*-
##
## $Id: pages.py,v 1.7 2009/04/28 14:07:40 dmartinc Exp $
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

from MaKaC.plugins.Collaboration.base import WCSPageTemplateBase, WJSBase,\
    WCSCSSBase
from MaKaC.common.utils import formatDateTime
from MaKaC.webinterface.common.tools import strip_ml_tags, unescape_html
from MaKaC.plugins.Collaboration.CERNMCU.common import getCERNMCUOptionValueByName
from MaKaC.rb_location import CrossLocationQueries

class WNewBookingForm(WCSPageTemplateBase):
        
    def getVars(self):
        vars = WCSPageTemplateBase.getVars( self )
        
        vars["EventTitle"] = self._conf.getTitle()
        vars["EventDescription"] = unescape_html(strip_ml_tags( self._conf.getDescription())).strip()
        vars["DefaultStartDate"] = formatDateTime(self._conf.getAdjustedStartDate())
        vars["DefaultEndDate"] = formatDateTime(self._conf.getAdjustedEndDate())
        vars["MinStartDate"] = formatDateTime(self._conf.getAdjustedStartDate())
        vars["MaxEndDate"] = formatDateTime(self._conf.getAdjustedEndDate())
        
        return vars

class WMain (WJSBase):
    
    def getVars(self):
        vars = WJSBase.getVars( self )
    
        vars["MinStartDate"] = formatDateTime(self._conf.getAdjustedStartDate())
        vars["MaxEndDate"] = formatDateTime(self._conf.getAdjustedEndDate())
        
        if self._conf.getRoom():
            vars["IncludeInitialRoom"] = True
            vars["InitialRoomName"] = self._conf.getRoom().getName()
            if self._conf.getLocation():
                vars["InitialRoomInstitution"] = self._conf.getLocation().getName()
            else:
                vars["InitialRoomInstitution"] = ""
            
            #TODO: check this code, currently throws an exception 'cannot connect to room booking DB"
            #rooms = CrossLocationQueries.getRooms( roomName = self._conf.getRoom().getName() )
            
            vars["InitialRoomIP"] = "Please fill the IP Field!" #rooms[0].customAtts["H323 IP"]
            
        else:
            vars["IncludeInitialRoom"] = False
            vars["InitialRoomName"] = ""
            vars["InitialRoomInstitution"] = ""
            vars["InitialRoomIP"] = ""
        
        vars["CERNGatekeeperPrefix"] = getCERNMCUOptionValueByName("CERNGatekeeperPrefix")
        vars["GDSPrefix"] = getCERNMCUOptionValueByName("GDSPrefix")
        vars["MCU_IP"] = getCERNMCUOptionValueByName("MCU_IP")
        vars["Phone_number"] = getCERNMCUOptionValueByName("Phone_number")
    
        return vars
    
class WIndexing(WJSBase):
    pass
    
class WExtra (WJSBase):
    def getVars(self):
        vars = WJSBase.getVars( self )
        return vars
    
class WStyle (WCSCSSBase):
    pass