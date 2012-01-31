# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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

import MaKaC.webinterface.pages.files as files
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.webinterface.rh.base import RHDisplayBaseProtected
from MaKaC.webinterface.rh.conferenceBase import RHFileBase

class RHFileDisplayBase( RHFileBase, RHDisplayBaseProtected ):
    
    def _checkParams( self, params ):
        RHFileBase._checkParams( self, params )

    def _checkProtection( self ):
        RHDisplayBaseProtected._checkProtection( self )

#class RHFileDisplayModificationBase( RHFileDisplayBase ):
#
#    def _checkParams( self, params ):
#        RHFileDisplayBase._checkParams( self, params )
#        cfaMgr = self._conf.getAbstractMgr()
#        id = ""
#        if params.has_key("abstractId"):
#            id = params["abstractId"]
#        elif params.has_key("contribId"):
#            id = params["contribId"]
#        self._abstract = self._target = cfaMgr.getAbstractById( id )
#    
#class RHFileDisplayModification( RHFileDisplayModificationBase ):
#    _uh = urlHandlers.UHFileDisplayModification
#    
#    def _process( self ):
#        p = files.WPFileDisplayModification( self, self._file )
#        return p.display()
#
#class RHFileDisplayDataModification( RHFileDisplayModificationBase ):
#    _uh = urlHandlers.UHFileDisplayDataModification
#    
#    def _process( self ):
#        p = files.WPFileDisplayDataModification( self, self._file )
#        return p.display()
#
#class RHFileDisplayPerformDataModification( RHFileDisplayModificationBase ):
#    _uh = urlHandlers.UHFileDisplayPerformDataModification
#    
#    def _process( self ):
#        fileData = self._getRequestParams()
#        self._file.setName( fileData["title"] )
#        self._file.setDescription( fileData["description"] )
#        self._redirect( urlHandlers.UHFileDisplayModification.getURL( self._file ) )
