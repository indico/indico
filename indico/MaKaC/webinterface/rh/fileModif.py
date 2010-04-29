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

import MaKaC.webinterface.pages.files as files
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.user as user
from MaKaC.webinterface.rh.conferenceBase import RHFileBase
from MaKaC.webinterface.rh.base import RHModificationBaseProtected

class RHFileModifBase( RHFileBase, RHModificationBaseProtected ):
    
    def _checkParams( self, params ):
        RHFileBase._checkParams( self, params )

    def _checkProtection( self ):
        if self._file.getSession() != None:
            if self._file.getSession().canCoordinate(self.getAW(), "modifContribs"):
                return
        RHModificationBaseProtected._checkProtection( self )
    
    def _displayCustomPage( self, wf ):
        return None

    def _displayDefaultPage( self ):
        return None

    def _process( self ):
        wf = self.getWebFactory()
        if wf != None:
            res = self._displayCustomPage( wf )
            if res != None:
                return res
        return self._displayDefaultPage()


class RHFileModification( RHFileModifBase ):
    _uh = urlHandlers.UHFileModification
    
    def _process( self ):
        p = files.WPFileModification( self, self._file )
        return p.display()


class RHFileModifyData( RHFileModifBase ):
    _uh = urlHandlers.UHFileModifyData
    
    def _process( self ):
        p = files.WPFileDataModification( self, self._file )
        return p.display()


class RHFilePerformModifyData( RHFileModifBase ):
    _uh = urlHandlers.UHFilePerformModifyData
    
    def _process( self ):
        fileData = self._getRequestParams()
        title="[not title assigned]"
        if fileData.get("title", "").strip() != "":
           title=fileData.get("title") 
        self._file.setName( title )
        self._file.setDescription( fileData["description"] )
        self._redirect( urlHandlers.UHFileModification.getURL( self._file ) )


class RHFileModifAC( RHFileModifBase ):
    _uh = urlHandlers.UHFileModifAC
    
    def _process( self ):
        p = files.WPFileModifAC( self, self._file )
        return p.display()


class RHFileSetVisibility( RHFileModifBase ):
    _uh = urlHandlers.UHFileSetVisibility
    
    def _checkParams( self, params ):
        RHFileModifBase._checkParams( self, params )
        privacy = params.get("visibility","PUBLIC")
        self._protect = 0
        if privacy == "PRIVATE":
            self._protect = 1
        elif privacy == "PUBLIC":
            self._protect = 0
        elif privacy == "ABSOLUTELY PUBLIC":
            self._protect = -1
            
    def _process( self ):
        self._file.setProtection( self._protect )
        self._redirect( urlHandlers.UHFileModifAC.getURL( self._file ) )


class RHFileSelectAllowed( RHFileModifBase ):
    _uh = urlHandlers.UHFileSelectAllowed
    
    def _process( self ):
        p = files.WPFileSelectAllowed( self, self._file )
        return p.display( **self._getRequestParams() )


class RHFileAddAllowed( RHFileModifBase ):
    _uh = urlHandlers.UHFileAddAllowed
    
    def _checkParams( self, params ):
        RHFileModifBase._checkParams( self, params )
        selAllowedId = self._normaliseListParam( params.get( "selectedPrincipals", [] ) )
        #ah = user.AvatarHolder()
        ph = user.PrincipalHolder()
        self._allowed = []
        for id in selAllowedId:
            self._allowed.append( ph.getById( id ) )
    
    def _process( self ):
        for av in self._allowed:
            self._target.grantAccess( av )
        self._redirect( urlHandlers.UHFileModifAC.getURL( self._file ) )


class RHFileRemoveAllowed( RHFileModifBase ):
    _uh = urlHandlers.UHFileRemoveAllowed

    def _checkParams( self, params ):
        RHFileModifBase._checkParams( self, params )
        selAllowedId = self._normaliseListParam( params.get( "selectedPrincipals", [] ) )
        #ah = user.AvatarHolder()
        ph = user.PrincipalHolder()
        self._allowed = []
        for id in selAllowedId:
            self._allowed.append( ph.getById( id ) )
    
    def _process( self ):
        for av in self._allowed:
            self._target.revokeAccess( av )
        self._redirect( urlHandlers.UHFileModifAC.getURL( self._file ) )
