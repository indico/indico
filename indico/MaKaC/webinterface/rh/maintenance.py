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

import MaKaC.webinterface.rh.admins as admins
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.common.general import *
from MaKaC.common.maintenanceMng import MaintenanceMng
from MaKaC.common import Config
from MaKaC.webinterface.pages import admins as adminPages
from MaKaC.common.db import DBMgr


class RHMaintenanceBase(admins.RHAdminBase):
    pass

class RHMaintenance( RHMaintenanceBase ):
    _uh = urlHandlers.UHMaintenance
    
    def _process( self ):
        s = MaintenanceMng.getStat(Config.getInstance().getTempDir())
        dbSize = MaintenanceMng.humanReadableSize(DBMgr.getInstance().getDBSize(), 'm')
        nWebsession = MaintenanceMng.getWebsessionNum()
        p = adminPages.WPMaintenance( self, s, dbSize, nWebsession)
        return p.display()

class RHMaintenanceTmpCleanup( RHMaintenanceBase ):
    _uh = urlHandlers.UHMaintenanceTmpCleanup
    
    def _process( self ):
        p = adminPages.WPMaintenanceTmpCleanup( self )
        return p.display()

class RHMaintenancePerformTmpCleanup( RHMaintenanceBase ):
    _uh = urlHandlers.UHMaintenancePerformTmpCleanup

    def _checkParams(self, params):
        RHMaintenanceBase._checkParams(self, params)
        self._confirmed=params.has_key("confirm")
        self._cancel=params.has_key("cancel")
    
    def _process( self ):
        if not self._cancel:
            if not self._confirmed:
                p=RHMaintenanceTmpCleanup(self)
                return p.display()
            MaintenanceMng.cleanupTmp(Config.getInstance().getTempDir())
        self._redirect(urlHandlers.UHMaintenance.getURL())

class RHMaintenancePack( RHMaintenanceBase ):
    _uh = urlHandlers.UHMaintenancePack
    
    def _process( self ):
        p = adminPages.WPMaintenancePack( self )
        return p.display()

class RHMaintenancePerformPack( RHMaintenanceBase ):
    _uh = urlHandlers.UHMaintenancePerformPack

    def _checkParams(self, params):
        RHMaintenanceBase._checkParams(self, params)
        self._confirmed=params.has_key("confirm")
        self._cancel=params.has_key("cancel")
    
    def _process( self ):
        if not self._cancel:
            if not self._confirmed:
                p=RHMaintenancePack(self)
                return p.display()
            DBMgr.getInstance().pack()
        self._redirect(urlHandlers.UHMaintenance.getURL())

class RHMaintenanceWebsessionCleanup( RHMaintenanceBase ):
    _uh = urlHandlers.UHMaintenancePack
    
    def _process( self ):
        p = adminPages.WPMaintenanceWebsessionCleanup( self )
        return p.display()

class RHMaintenancePerformWebsessionCleanup( RHMaintenanceBase ):
    _uh = urlHandlers.UHMaintenancePerformPack

    def _checkParams(self, params):
        RHMaintenanceBase._checkParams(self, params)
        self._confirmed=params.has_key("confirm")
        self._cancel=params.has_key("cancel")
    
    def _process( self ):
        if not self._cancel:
            if not self._confirmed:
                p=RHMaintenancePack(self)
                return p.display()
            MaintenanceMng.cleanupWebsession()
        self._redirect(urlHandlers.UHMaintenance.getURL())
