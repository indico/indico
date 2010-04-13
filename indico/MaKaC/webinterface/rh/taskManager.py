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

from MaKaC.common.pendingQueues import PendingSubmitterReminder, PendingManagerReminder, PendingCoordinatorReminder, ConfPendingQueuesMgr
from MaKaC.common.timerExec import HelperTaskList, Alarm


class RHTaskManagerBase(admins.RHAdminBase):
    pass

class RHTaskManager( RHTaskManagerBase ):
    _uh = urlHandlers.UHTaskManager
    
    def _process( self ):
        
        p = adminPages.WPTaskManager( self)
        return p.display()

class RHRemoveTask( RHTaskManagerBase ):
    _uh = urlHandlers.UHRemoveTask
    
    def _checkParams(self, params):
        RHTaskManagerBase._checkParams(self, params)
        self._confirmed=params.has_key("confirm")
        self._cancel=params.has_key("cancel")
        self._taskId = params.get("taskId", None)
    
    def _process( self ):
        if self._cancel or not self._taskId:
            self._redirect(urlHandlers.UHTaskManager.getURL())
        elif self._confirmed:
            self._deleteTask(self._taskId)
            self._redirect(urlHandlers.UHTaskManager.getURL())
        else:
            p = adminPages.WPConfirmDelete(self, self._taskId)
            return p.display()
    
    def _deleteTask(self, taskId):
        task = HelperTaskList.getTaskListInstance().getTaskById(taskId)
        
        if isinstance(task, Alarm):
            task.conf.removeAlarm(task)
            return
        else:
            if type(task.getObjList()[0]) == PendingSubmitterReminder: 
                for obj in task.getObjList():
                    for pend in obj.getPendings():
                        cpqm = pend.getConference().getPendingQueuesMgr()
                        cpqm.removePendingSubmitter(pend)
                    task.removeObj(obj)
                return
            elif type(task.getObjList()[0]) == PendingManagerReminder:
                for obj in task.getObjList():
                    for pend in obj.getPendings():
                        cpqm = pend.getConference().getPendingQueuesMgr()
                        cpqm.removePendingManager(pend)
                    task.removeObj(obj)
                return
            elif type(task.getObjList()[0]) == PendingCoordinatorReminder:
                for obj in task.getObjList():
                    for pend in obj.getPendings():
                        cpqm = pend.getConference().getPendingQueuesMgr()
                        cpqm.removePendingCoordinator(pend)
                    task.removeObj(obj)
                return

################################################
##
##class RHMaintenanceTmpCleanup( RHMaintenanceBase ):
##    _uh = urlHandlers.UHMaintenanceTmpCleanup
##    
##    def _process( self ):
##        p = maintenance.WPMaintenanceTmpCleanup( self )
##        return p.display()
##
##class RHMaintenancePerformTmpCleanup( RHMaintenanceBase ):
##    _uh = urlHandlers.UHMaintenancePerformTmpCleanup
##
##    def _checkParams(self, params):
##        RHMaintenanceBase._checkParams(self, params)
##        self._confirmed=params.has_key("confirm")
##        self._cancel=params.has_key("cancel")
##    
##    def _process( self ):
##        if not self._cancel:
##            if not self._confirmed:
##                p=maintenance.RHMaintenanceTmpCleanup(self)
##                return p.display()
##            MaintenanceMng.cleanupTmp(Config.getInstance().getTempDir())
##        self._redirect(urlHandlers.UHMaintenance.getURL())
##
##class RHMaintenancePack( RHMaintenanceBase ):
##    _uh = urlHandlers.UHMaintenancePack
##    
##    def _process( self ):
##        p = maintenance.WPMaintenancePack( self )
##        return p.display()
##
##class RHMaintenancePerformPack( RHMaintenanceBase ):
##    _uh = urlHandlers.UHMaintenancePerformPack
##
##    def _checkParams(self, params):
##        RHMaintenanceBase._checkParams(self, params)
##        self._confirmed=params.has_key("confirm")
##        self._cancel=params.has_key("cancel")
##    
##    def _process( self ):
##        if not self._cancel:
##            if not self._confirmed:
##                p=maintenance.RHMaintenancePack(self)
##                return p.display()
##            DBMgr.getInstance().pack()
##        self._redirect(urlHandlers.UHMaintenance.getURL())
##
##class RHMaintenanceWebsessionCleanup( RHMaintenanceBase ):
##    _uh = urlHandlers.UHMaintenancePack
##    
##    def _process( self ):
##        p = maintenance.WPMaintenanceWebsessionCleanup( self )
##        return p.display()
##
##class RHMaintenancePerformWebsessionCleanup( RHMaintenanceBase ):
##    _uh = urlHandlers.UHMaintenancePerformPack
##
##    def _checkParams(self, params):
##        RHMaintenanceBase._checkParams(self, params)
##        self._confirmed=params.has_key("confirm")
##        self._cancel=params.has_key("cancel")
##    
##    def _process( self ):
##        if not self._cancel:
##            if not self._confirmed:
##                p=maintenance.RHMaintenancePack(self)
##                return p.display()
##            MaintenanceMng.cleanupWebsession()
##        self._redirect(urlHandlers.UHMaintenance.getURL())
