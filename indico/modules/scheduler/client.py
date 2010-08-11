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

from indico.modules.scheduler import SchedulerModule

class Client(object):

    """
    :py:class:`~indico.modules.scheduler.Client` provices a transparent scheduler
    client, that allows Indico client processes to interact with the Scheduler
    without the need for a lot of code.

    It acts as a remote proxy.
    """

    def __init__(self):
        super(Client, self).__init__()
        self._schedMod = SchedulerModule.getDBInstance()

    def enqueue(self, task):
        """
        Schedules a task for execution
        """

        return self._schedMod.spool('add', task)

    def dequeue(self, task):
        """
        Schedules a task for execution
        """

        return self._schedMod.spool('del', task)

    def shutdown(self, msg = ""):
        """
        Shuts down the scheduler. `msg` is an optional paramater that provides
        an information message that will be written in the logs
        """

        return self._schedMod.spool('shutdown', msg)

    def clearSpool(self):
        """
        Clears the spool, returning the number of removed elements
        """
        return self._schedMod.clearSpool()

    def getSpool(self):
        """
        Returns the spool
        """
        return self._schedMod.getSpool()

    def getStatus(self):
        """
        Returns status information (dictionary), containing the lengths (tasks) of:
          * spool;
          * waiting queue;
          * running queue;
          * finished task index;
          * failed task index;

        As well as if the scheduler is running (`state`)
        """

        return self._schedMod.getStatus()

    def getTask(self, tid):
        """
        Returns a :py:class:`task <indico.modules.scheduler.tasks.BaseTask>` object,
        given its task id
        """

        return self._schedMod.getTaskIndex()[tid]
