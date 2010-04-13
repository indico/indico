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

import MaKaC.webinterface.pages.links as links
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.webinterface.rh.base import RHDisplayBaseProtected
from MaKaC.webinterface.rh.conferenceBase import RHLinkBase

class RHLinkDisplayBase( RHLinkBase, RHDisplayBaseProtected ):
    
    def _checkParams( self, params ):
        RHLinkBase._checkParams( self, params )

    def _checkProtection( self ):
        RHDisplayBaseProtected._checkProtection( self )

#class RHLinkDisplayModificationBase( RHLinkDisplayBase ):
#
#    def _checkParams( self, params ):
#        RHLinkDisplayBase._checkParams( self, params )
#        cfaMgr = self._conf.getAbstractMgr()
#        id = ""
#        if params.has_key("abstractId"):
#            id = params["abstractId"]
#        elif params.has_key("contribId"):
#            id = params["contribId"]
#        self._abstract = self._target = cfaMgr.getAbstractById( id )
#    
#class RHLinkDisplayModification( RHLinkDisplayModificationBase ):
#    _uh = urlHandlers.UHLinkDisplayModification
#    
#    def _process( self ):
#        p = links.WPLinkDisplayModification( self, self._link )
#        return p.display()

#class RHLinkDisplayDataModification( RHLinkDisplayModificationBase ):
#    _uh = urlHandlers.UHLinkDisplayDataModification
#    
#    def _process( self ):
#        p = links.WPLinkDisplayDataModification( self, self._link )
#        return p.display()
#
#class RHLinkDisplayPerformDataModification( RHLinkDisplayModificationBase ):
#    _uh = urlHandlers.UHLinkDisplayPerformDataModification
#    
#    def _process( self ):
#        linkData = self._getRequestParams()
#        self._link.setName( linkData["title"] )
#        self._link.setDescription( linkData["description"] )
#        self._link.setURL( linkData["url"] )
#        self._redirect( urlHandlers.UHLinkDisplayModification.getURL( self._link ) )
