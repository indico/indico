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

import MaKaC.webinterface.pages.links as links
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.user as user
from MaKaC.webinterface.rh.conferenceBase import RHLinkBase
from MaKaC.webinterface.rh.base import RHModificationBaseProtected


class RHLinkModifBase( RHLinkBase, RHModificationBaseProtected ):
    
    def _checkParams( self, params ):
        RHLinkBase._checkParams( self, params )

    def _checkProtection( self ):
        if self._link.getSession() != None:
            if self._link.getSession().canCoordinate(self.getAW(), "modifContribs"):
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


class RHLinkModification( RHLinkModifBase ):
    _uh = urlHandlers.UHLinkModification
    
    def _process( self ):
        p = links.WPLinkModification( self, self._link )
        return p.display()


class RHLinkModifyData( RHLinkModifBase ):
    _uh = urlHandlers.UHLinkModifyData
    
    def _process( self ):
        p = links.WPLinkDataModification( self, self._link )
        return p.display()


class RHLinkPerformModifyData( RHLinkModifBase ):
    _uh = urlHandlers.UHLinkPerformModifyData
    
    def _process( self ):
        linkData = self._getRequestParams()
        self._link.setName( linkData["title"] )
        self._link.setDescription( linkData["description"] )
        self._link.setURL( linkData["url"] )
        self._redirect( urlHandlers.UHLinkModification.getURL( self._link ) )


class RHLinkModifAC( RHLinkModifBase ):
    _uh = urlHandlers.UHLinkModifAC
    
    def _process( self ):
        p = links.WPLinkModifAC( self, self._link )
        return p.display()


class RHLinkSetVisibility( RHLinkModifBase ):
    _uh = urlHandlers.UHLinkSetVisibility
    
    def _checkParams( self, params ):
        RHLinkModifBase._checkParams( self, params )
        privacy = params.get("visibility","PUBLIC")
        self._protect = 0
        if privacy == "PRIVATE":
            self._protect = 1
        elif privacy == "PUBLIC":
            self._protect = 0
        elif privacy == "ABSOLUTELY PUBLIC":
            self._protect = -1
    
    def _process( self ):
        self._link.setProtection( self._protect )
        self._redirect( urlHandlers.UHLinkModifAC.getURL( self._link ) )


class RHLinkSelectAllowed( RHLinkModifBase ):
    _uh = urlHandlers.UHLinkSelectAllowed
    
    def _process( self ):
        p = links.WPLinkSelectAllowed( self, self._link )
        return p.display( **self._getRequestParams() )


class RHLinkAddAllowed( RHLinkModifBase ):
    _uh = urlHandlers.UHLinkAddAllowed
    
    def _checkParams( self, params ):
        RHLinkModifBase._checkParams( self, params )
        selAllowedId = self._normaliseListParam( params.get( "selectedPrincipals", [] ) )
        ah = user.AvatarHolder()
        self._allowed = []
        for id in selAllowedId:
            self._allowed.append( ah.getById( id ) )
    
    def _process( self ):
        for av in self._allowed:
            self._target.grantAccess( av )
        self._redirect( urlHandlers.UHLinkModifAC.getURL( self._link ) )


class RHLinkRemoveAllowed( RHLinkModifBase ):
    _uh = urlHandlers.UHLinkRemoveAllowed

    def _checkParams( self, params ):
        RHLinkModifBase._checkParams( self, params )
        selAllowedId = self._normaliseListParam( params.get( "selectedPrincipals", [] ) )
        ah = user.AvatarHolder()
        self._allowed = []
        for id in selAllowedId:
            self._allowed.append( ah.getById( id ) )
    
    def _process( self ):
        for av in self._allowed:
            self._target.revokeAccess( av )
        self._redirect( urlHandlers.UHLinkModifAC.getURL( self._link ) )
