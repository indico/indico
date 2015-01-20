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

import MaKaC.webinterface.pages.admins as adminPages
import MaKaC.roomMapping as roomMapping
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.rh.admins as admins
from MaKaC.webinterface import locators
from MaKaC.errors import AccessError


class RHRoomMapperProtected( admins.RHAdminBase ):
    def _checkProtection( self ):
        if self._getUser() is None:
            self._checkSessionUser()
        elif not self._getUser().isRBAdmin():
            raise AccessError( "You are not authorized to take this action." )

class RHRoomMappers( RHRoomMapperProtected ):
    _uh = urlHandlers.UHRoomMappers

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._params = params

    def _process( self ):
        p = adminPages.WPRoomMapperList( self, self._params )
        return p.display()


class RHRoomMapperBase( RHRoomMapperProtected ):

    def _checkParams( self, params ):
        RHRoomMapperProtected._checkParams( self, params )
        self._roomMapper = locators.RoomMapperWebLocator( params ).getObject()
        self._doNotSanitizeFields.append("regexps")


class RHRoomMapperDetails( RHRoomMapperBase ):
    _uh = urlHandlers.UHRoomMapperDetails

    def _process( self ):
        p = adminPages.WPRoomMapperDetails( self, self._roomMapper )
        return p.display()


class RHRoomMapperModification( RHRoomMapperBase ):
    _uh = urlHandlers.UHRoomMapperModification

    def _process( self ):
        p = adminPages.WPRoomMapperModification( self, self._roomMapper )
        return p.display()


class RHRoomMapperPerformModification( RHRoomMapperBase ):
    _uh = urlHandlers.UHRoomMapperPerformModification

    def _process( self ):
        self._roomMapper.setValues(self._getRequestParams())
        self._redirect( urlHandlers.UHRoomMapperDetails.getURL( self._roomMapper ) )


class RHRoomMapperCreation( RHRoomMapperProtected ):
    _uh = urlHandlers.UHNewRoomMapper

    def _process( self ):
        p = adminPages.WPRoomMapperCreation( self )
        return p.display()


class RHRoomMapperPerformCreation( RHRoomMapperProtected ):
    _uh = urlHandlers.UHRoomMapperPerformCreation

    def _process( self ):
        rm = roomMapping.RoomMapper()
        rm.setValues(self._getRequestParams())
        rmh = roomMapping.RoomMapperHolder()
        rmh.add( rm )
        self._redirect( urlHandlers.UHRoomMapperDetails.getURL( rm ) )
