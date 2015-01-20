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


