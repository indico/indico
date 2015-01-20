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

import MaKaC.webinterface.rh.admins as admins
import MaKaC.webinterface.pages.admins as adminPages
import MaKaC.user as user
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.errors as errors
from MaKaC.authentication.LDAPAuthentication import LDAPGroup
from MaKaC.errors import MaKaCError
from MaKaC.webinterface.rh.base import RHProtected
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


class _GroupUtils:

    def setGroupValues( self, grp, grpData ):
        grp.setName( grpData["name"] )
        grp.setDescription( grpData["description"] )
        grp.setEmail( grpData["email"] )
        grp.setObsolete( grpData.has_key("obsolete") )
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
        if not isinstance(self._group, LDAPGroup):
            _GroupUtils.setGroupValues( self._group, self._grpData )
        else:
            self._group.setObsolete(self._grpData.has_key('obsolete'))
        self._redirect( urlHandlers.UHGroupDetails.getURL( self._group ) )
