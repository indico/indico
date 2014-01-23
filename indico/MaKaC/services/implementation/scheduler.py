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

"""
AJAX Services for Scheduler (admin)
"""

from MaKaC.services.implementation.base import AdminService
from MaKaC.services.interface.rpc.common import ServiceError

from indico.modules import ModuleHolder
from indico.modules.scheduler import Client
from indico.util import fossilize, date_time


class SchedulerModuleAdminService(AdminService):

    def _checkParams(self):
        AdminService._checkParams(self)
        self.schedModule = ModuleHolder().getById('scheduler')


class GetSchedulerSummary(SchedulerModuleAdminService):
    """
    Returns a summary of the status of the scheduler daemon
    """

    def _getAnswer(self):
        return fossilize.fossilize(self.schedModule.getStatus())


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
        return fossilize.fossilize(self.schedModule.getFailedIndex().values())


class GetFinishedTaskList(SchedulerModuleAdminService):
    """
    Returns the list of tasks that have successfully finished their execution
    """

    def _checkParams(self):
        SchedulerModuleAdminService._checkParams(self)
        self._criteria = dict((k,v) for (k,v) in
                              self._params.iteritems() if k in ['ndays'])

    def _getAnswer(self):

        idx = self.schedModule.getFinishedIndex()

        if len(idx) > 0:
            # 1 day
            ts = idx.maxKey() - 24*60*60

            return fossilize.fossilize(
                idx.itervalues(ts))
        else:
            return {}


class TaskAdminService(SchedulerModuleAdminService):
    """
    Common to all tasks
    """

    def _checkParams(self):
        SchedulerModuleAdminService._checkParams(self)
        tid = self._params.get('id', None)

        if tid == None:
            raise ServiceError('ERR-T0','Task Id not provided')

        self._client = Client()
        self._task = self._client.getTask(tid)


class DeleteTask(TaskAdminService):
    """
    Deletes a task
    """

    def _getAnswer(self):
        self._client.dequeue(self._task)


class RunFailedTask(TaskAdminService):
    """
    Runs a (failed) task now
    """

    def _getAnswer(self):

        self._task.setStartOn(date_time.nowutc())
        self._client.startFailedTask(self._task)

methodMap = {
    "summary": GetSchedulerSummary,
    "tasks.listWaiting": GetWaitingTaskList,
    "tasks.listRunning": GetRunningTaskList,
    "tasks.listFailed": GetFailedTaskList,
    "tasks.listFinished": GetFinishedTaskList,
    "tasks.delete" : DeleteTask,
    "tasks.runFailed" : RunFailedTask
    }
