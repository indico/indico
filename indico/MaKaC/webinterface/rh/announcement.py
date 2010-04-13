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

from MaKaC.webinterface.rh.admins import RHAdminBase
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.common.Announcement import getAnnoucementMgrInstance
import MaKaC.webinterface.pages.admins as admins


class RHAnnouncementModif(RHAdminBase):
    
    def _process( self ):
        p = admins.WPAnnouncementModif( self )
        return p.display()

class RHAnnouncementModifSave(RHAdminBase):
    
    def _checkParams( self, params ):
        RHAdminBase._checkParams( self, params )
        self.text = params.get("announcement", "")
        
    
    def _process( self ):
        an = getAnnoucementMgrInstance()
        an.setText(self.text)
        self._redirect(urlHandlers.UHAnnouncement.getURL())
            
        
