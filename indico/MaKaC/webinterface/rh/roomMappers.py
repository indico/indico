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

import MaKaC.webinterface.pages.admins as adminPages
import MaKaC.roomMapping as roomMapping
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.errors as erros
import MaKaC.webinterface.rh.admins as admins
from MaKaC.webinterface import locators


class RHRoomMapperProtected( admins.RHAdminBase ):
    pass

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
        
    
    



