# -*- coding: utf-8 -*-
##
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

from MaKaC.webinterface.pages.main import WPMainBase
import MaKaC.webinterface.wcomponents as wcomponents      
from MaKaC.modules.base import ModulesHolder
from MaKaC.i18n import _
from pytz import timezone
from MaKaC.common import timezoneUtils

class WPNews(WPMainBase):

    def _getBody(self, params):
        wc = WNews(tz = timezone(timezoneUtils.DisplayTZ(self._getAW()).getDisplayTZ()))
        return wc.getHTML()
    
    def _getTitle(self):
        return WPMainBase._getTitle(self) + " - " + _("News")


class WNews(wcomponents.WTemplated):
    
    def __init__(self, tz):
        wcomponents.WTemplated.__init__(self)
        self._tz = tz

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        
        newsModule = ModulesHolder().getById("news")
        vars["news"] = newsModule.getNewsItemsList()
        vars["tz"] = self._tz
        
        return vars
        
