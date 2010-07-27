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

"""
AJAX Services for Scheduler (admin)
"""

from MaKaC.services.implementation.base import AdminService

from indico.modules import ModuleHolder
from indico.util import fossilize


class SchedulerModuleAdminService(AdminService):

    def _checkParams(self):
        AdminService._checkParams(self)
        self.schedModule = ModuleHolder().getById('scheduler')


class GetWaitingTaskList(SchedulerModuleAdminService):
    """
    Returns the list of tasks currently waiting to be executed
    """

    def _getAnswer(self):
        return fossilize.fossilize(list(v for (k,v) in
                                        self.schedModule.getWaitingQueue()))


class GetRunningTaskList(SchedulerModuleAdminService):
    """
    Returns the list of tasks currently running
    """

    def _getAnswer(self):
        return fossilize.fossilize(self.schedModule.getRunningList())


class GetFailedTaskList(SchedulerModuleAdminService):
    """
    Returns the list of tasks currently running
    """

    def _getAnswer(self):
        failedIds = self.schedModule.getFailedIndex().all()
        taskIdx = self.schedModule.getTaskIndex()

        return fossilize.fossilize(list((taskIdx[k] for k in failedIds)))


class GetFinishedTaskList(SchedulerModuleAdminService):
    """
    Returns the list of tasks that have successfully finished their execution
    """

    def _getAnswer(self):
        finishedIds = self.schedModule.getFinishedIndex().all()
        taskIdx = self.schedModule.getTaskIndex()

        return fossilize.fossilize(list((taskIdx[k] for k in finishedIds)))


methodMap = {
    "tasks.listWaiting": GetWaitingTaskList,
    "tasks.listRunning": GetRunningTaskList,
    "tasks.listFailed": GetFailedTaskList,
    "tasks.listFinished": GetFinishedTaskList
    }
