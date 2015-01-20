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
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.common.maintenanceMng import MaintenanceMng
from indico.core.config import Config
from MaKaC.webinterface.pages import admins as adminPages
from indico.core.db import DBMgr


class RHMaintenanceBase(admins.RHAdminBase):
    pass

class RHMaintenance( RHMaintenanceBase ):
    _uh = urlHandlers.UHMaintenance

    def _process( self ):
        s = MaintenanceMng.getStat(Config.getInstance().getTempDir())
        dbSize = MaintenanceMng.humanReadableSize(DBMgr.getInstance().getDBSize(), 'm')
        p = adminPages.WPMaintenance( self, s, dbSize)
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
