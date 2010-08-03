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

import time, logging

from indico.modules.scheduler import SchedulerModule, base
from MaKaC.common import DBMgr


class Worker(base._MT_UNIT):

    def __init__(self, taskId, configData):
        super(Worker, self).__init__()

        self._logger = logging.getLogger('worker/%s' % taskId)
        self.success = None
        self._taskId = taskId
        self._config = configData

    def _prepare(self):
        """
        This acts as a second 'constructor', that is executed in the
        context of the thread (due to database reasons)
        """
        self._dbi = DBMgr.getInstance()
        self._dbi.startRequest()
        schedMod = SchedulerModule.getDBInstance()
        self._task = schedMod.getTaskById(self._taskId)

        # open a logging channel
        self._task.plugLogger(self._logger)

        self._dbi.endRequest()

    def run(self):

        self._prepare()

        self._logger.debug('Running task %s..' % self._task.id)

        # We will try to run the task TASK_MAX_RETRIES
        # times and if it continues failing we abort it
        i = 0

        self._dbi.startRequest()

        while i < self._config.task_max_tries and not self._task.endedOn:
            i = i + 1
            try:
                self._task.start()

            except Exception, e:
                nextRunIn = i * 10 # secs
                self._logger.warning("Task %s failed with exception '%s'. "
                                     "Retrying for the %dth time in %d secs.." %
                                     (self._task.id, e, i + 1, nextRunIn))

                self._logger.exception('Error message')

                if  i < self._config.task_max_tries:
                    # if i is still low enough, we sleep progressively more
                    # so that if the error is caused by concurrency we don't make
                    # the problem worse by hammering the server.
                    time.sleep(nextRunIn)

                # abort transaction and synchronize
                self._dbi.sync()
            else:
                break

        self._logger.info('Ended on: %s' % self._task.endedOn)

        if self._task.endedOn: # task successfully finished
            self.success = True
            if i > 1:
                self._logger.warning("Task %s failed %d times before "
                                     "finishing correctly" % (self._task.id, i - 1))
        else:
            self.success = False
            self._logger.error("Task %s failed too many (%d) times. "
                               "Aborting its execution.." % (self._task.id, i))

        self._dbi.endRequest()
