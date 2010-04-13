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
import MaKaC.webinterface.rh.admins as admins
import MaKaC.common.info as info
import MaKaC.webinterface.urlHandlers as urlHandlers

class RHRoomBookingPluginAdminBase( admins.RHAdminBase ):
    pass

class RHRoomBookingPluginAdmin( RHRoomBookingPluginAdminBase ):

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._params = params

    def _process( self ):
        p = adminPages.WPRoomBookingPluginAdmin( self, self._params )
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        self._host, self._port = minfo.getRoomBookingDBConnectionParams()
        self._realm = minfo.getRoomBookingDBRealm()
        self._user = minfo.getRoomBookingDBUserName()
        self._password = minfo.getRoomBookingDBPassword()
        return p.display()

class RHSwitchRoomBookingModuleActive( RHRoomBookingPluginAdminBase ):

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._params = params

    def _process( self ):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        
        active = minfo.getRoomBookingModuleActive()
        if not active:
            # Initialize built-in plugin on activation
            from MaKaC.plugins.RoomBooking.CERN.initialize import initializeRoomBookingDB 
            from MaKaC.plugins.RoomBooking.CERN.dalManagerCERN import DALManagerCERN
            DALManagerCERN.connect()
            initializeRoomBookingDB( "Universe", force = False ) # Safe if data present
            DALManagerCERN.disconnect()
            
        minfo.setRoomBookingModuleActive( not active )

        self._redirect( urlHandlers.UHRoomBookingPluginAdmin.getURL() )

class RHZODBSave( RHRoomBookingPluginAdminBase ):

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        
        self._host = params.get('ZODBHost','')
        self._port = int( params.get('ZODBPort','') )
        self._realm = params.get('ZODBRealm', "")
        self._user = params.get('ZODBUser', "")
        self._password = params.get('ZODBPassword', "")

        self._params = params

    def _process( self ):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        minfo.setRoomBookingDBConnectionParams( ( self._host, self._port ) )
        minfo.setRoomBookingDBRealm( self._realm )
        minfo.setRoomBookingDBUserName( self._user )
        minfo.setRoomBookingDBPassword( self._password )
        self._redirect( urlHandlers.UHRoomBookingPluginAdmin.getURL() )
