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

import MaKaC.webinterface.rh.base as base
import MaKaC.webinterface.rh.admins as admins
import MaKaC.webinterface.pages.admins as adminPages
import MaKaC.user as user
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.errors as errors
from MaKaC.common.general import *
from MaKaC.errors import MaKaCError
from MaKaC.webinterface.rh.base import RH, RHProtected
from MaKaC.i18n import _

class RHGroupsProtected(admins.RHAdminBase):
    pass

class RHGroups( RHGroupsProtected ):
    _uh = urlHandlers.UHGroups
    
    def _checkParams(self,params):
        admins.RHAdminBase._checkParams(self,params)
        self._params = params
        
    def _process( self ):
        p = adminPages.WPGroupList( self, self._params )
        return p.display()


class RHGroupCreation( RHGroupsProtected ):
    _uh = urlHandlers.UHNewGroup
    
    def _process( self ):
        p = adminPages.WPGroupCreation( self )
        return p.display()

class RHLDAPGroupCreation( RHGroupsProtected ):
    _uh = urlHandlers.UHNewGroup
    
    def _process( self ):
        p = adminPages.WPLDAPGroupCreation( self )
        return p.display()


class _GroupUtils:
    
    def setGroupValues( self, grp, grpData ):
        grp.setName( grpData["name"] )
        grp.setDescription( grpData["description"] ) 
        grp.setEmail( grpData["email"] )
    setGroupValues = classmethod( setGroupValues )


class RHGroupPerformCreation( RHGroupsProtected ):
    _uh = urlHandlers.UHGroupPerformRegistration
    
    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams(self,params)
        self._grpData = params
    
    def _process( self ):
        grp = user.Group()
        _GroupUtils.setGroupValues( grp, self._grpData )
        gh = user.GroupHolder()
        gh.add( grp )        
        self._redirect( urlHandlers.UHGroupDetails.getURL( grp ) )


class RHGroupBase( RHGroupsProtected ):

    def _checkProtection( self ):
        if self._group.getMemberList() == []:
            return 
        RHProtected._checkProtection( self )
        if not self._group.canModify( self._aw ):
            raise errors.ModificationError("group")
    
    def _checkParams ( self, params ):
        admins.RHAdminBase._checkParams(self,params)
        if "groupId" not in params or params["groupId"].strip() == "":
            raise MaKaCError( _("group id not specified"))
        gh = user.GroupHolder()
        self._target = self._group = gh.getById( params["groupId"] )


class RHGroupDetails( RHGroupBase ):
    _uh = urlHandlers.UHGroupDetails
    
    def _process( self ):
        p = adminPages.WPGroupDetails( self, self._group )
        return p.display()


class RHGroupModification( RHGroupBase ):
    _uh = urlHandlers.UHGroupModification
    
    def _process( self ):
        p = adminPages.WPGroupModification( self, self._group )
        return p.display()


class RHGroupPerformModification( RHGroupBase ):
    _uh = urlHandlers.UHGroupPerformModification
    
    def _checkParams( self, params ):
        RHGroupBase._checkParams( self, params )
        self._grpData = params
    
    def _process( self ):
        if not isinstance(self._group, user.CERNGroup):
            _GroupUtils.setGroupValues( self._group, self._grpData )
        self._redirect( urlHandlers.UHGroupDetails.getURL( self._group ) )


class RHGroupSelectMembers( RHGroupBase ):
    _uh = urlHandlers.UHGroupSelectMembers
    
    def _process( self ):
        p = adminPages.WPGroupSelectMembers( self, self._group )
        return p.display( **self._getRequestParams() )


class RHGroupAddMembers( RHGroupBase ):
    _uh = urlHandlers.UHGroupAddMembers
    
    def _checkParams( self, params ):
        self._params = params
        RHGroupBase._checkParams( self, params )
        self._selMembersIdList = self._normaliseListParam( params.get("selectedPrincipals", []) )  
    
    def _process( self ):
        if not self._params.has_key("cancel") and not isinstance(self._group, user.CERNGroup):
            ah = user.PrincipalHolder() 
            for id in self._selMembersIdList:
                if id:
                    self._group.addMember( ah.getById( id ) )
        self._redirect( urlHandlers.UHGroupDetails.getURL( self._group ) )


class RHGroupRemoveMembers( RHGroupBase ):
    _uh = urlHandlers.UHGroupRemoveMembers
    
    def _checkParams( self, params ):
        RHGroupBase._checkParams( self, params )
        self._selMembersIdList = self._normaliseListParam( params.get("selectedPrincipals", []) )

    def _process( self ):
        ah = user.PrincipalHolder() 
        for id in self._selMembersIdList:
            self._group.removeMember( ah.getById( id ) )
        self._redirect( urlHandlers.UHGroupDetails.getURL( self._group ) )
