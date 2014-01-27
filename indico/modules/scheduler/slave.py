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

import time
import logging
import multiprocessing
import threading
import os
from ZODB.POSException import ConflictError
from indico.core.db import DBMgr
from MaKaC.common.mail import GenericMailer
from MaKaC.plugins.RoomBooking.default.dalManager import DBConnection, DALManager
from MaKaC.common.info import HelperMaKaCInfo
from indico.modules.scheduler import SchedulerModule, base, TaskDelayed
from indico.util import fossilize

class _Worker(object):

    def __init__(self, taskId, configData, delay):
        super(_Worker, self).__init__()

        self._logger = logging.getLogger('worker/%s' % taskId)
        self._taskId = taskId
        self._config = configData
        self._executionDelay = delay

        # Import it here to avoid circular import
        from indico.web.flask.app import make_app
        self._app = make_app(True)

    def _prepare(self):
        """
        This acts as a second 'constructor', that is executed in the
        context of the thread (due to database reasons)
        """

        self._prepareDB()
        self._dbi.startRequest()

        with self._dbi.transaction() as conn:
            schedMod = SchedulerModule.getDBInstance()
            self._task = schedMod.getTaskById(self._taskId)

            info = HelperMaKaCInfo.getMaKaCInfoInstance()
            self._rbEnabled = info.getRoomBookingModuleActive()

            if self._rbEnabled:
                self._rbdbi = DALManager.getInstance()
                self._rbdbi.connect()
            else:
                self._rbdbi = DALManager.dummyConnection()

            # open a logging channel
            self._task.plugLogger(self._logger)

    def _prepareDB(self):
        self._dbi = DBMgr.getInstance()

    def run(self):

        self._prepare()

        self._logger.info('Running task %s.. (delay: %s)' % (self._task.id, self._executionDelay))

        # We will try to run the task TASK_MAX_RETRIES
        # times and if it continues failing we abort it
        i = 0

        # RoomBooking forces us to connect to its own DB if needed
        # Maybe we should add some extension point here that lets plugins
        # define their own actions on DB connect/disconnect/commit/abort

        # potentially conflict-prone (!)
        with self._dbi.transaction(sync=True):
            with self._rbdbi.transaction():
                self._task.prepare()

        delayed = False
        while i < self._config.task_max_tries:
            # Otherwise objects modified in indico itself are not updated here
            if hasattr(self._rbdbi, 'sync'):
                self._rbdbi.sync()

            try:
                if i > 0:
                    self._dbi.abort()
                    # delete all queued emails
                    GenericMailer.flushQueue(False)
                    # restore logger
                    self._task.plugLogger(self._logger)

                with self._dbi.transaction():
                    with self._rbdbi.transaction():

                        self._logger.info('Task cycle %d' % i)
                        i = i + 1

                        # clear the fossile cache at the start of each task
                        fossilize.clearCache()

                        with self._app.app_context():
                            self._task.start(self._executionDelay)
                        break

            except TaskDelayed, e:
                nextRunIn = e.delaySeconds
                self._executionDelay = 0
                delayed = True
                self._logger.info("%s delayed by %d seconds" % (self._task, e.delaySeconds))
                base.TimeSource.get().sleep(nextRunIn)

            except Exception, e:
                self._logger.exception("%s failed with exception '%s'. " % \
                                       (self._task, e))

                if  i < self._config.task_max_tries:
                    nextRunIn = i * 10  # secs

                    self._logger.warning("Retrying for the %dth time in %d secs.." % \
                                         (i + 1, nextRunIn))

                    # if i is still low enough, we sleep progressively more
                    # so that if the error is caused by concurrency we don't make
                    # the problem worse by hammering the server.
                    base.TimeSource.get().sleep(nextRunIn)

        GenericMailer.flushQueue(True)

        self._logger.info('Ended on: %s' % self._task.endedOn)

        # task successfully finished
        if self._task.endedOn:
            with self._dbi.transaction():
                self._setResult(True)
            if i > (1 + int(delayed)):
                self._logger.warning("%s failed %d times before "
                                     "finishing correctly" % (self._task, i - int(delayed) - 1))
        else:
            with self._dbi.transaction():
                self._setResult(False)
            self._logger.error("%s failed too many (%d) times. "
                               "Aborting its execution.." % (self._task, i))

            self._logger.info("exiting")

        self._dbi.endRequest()


class ThreadWorker(_Worker, threading.Thread):

    def __init__(self, tid, configData, delay):
        super(ThreadWorker, self).__init__(tid, configData, delay)
        self._result = 0

    def _setResult(self, res):
        self._result = res

    def getResult(self):
        return self._result


class ProcessWorker(_Worker, multiprocessing.Process):

    def __init__(self, tid, configData, delay):
        super(ProcessWorker, self).__init__(tid, configData, delay)
        self._result = multiprocessing.Value('i', 0)

    def _prepareDB(self):
        # since the DBMgr instance will be replicated across objects,
        # we just set it as None for this one.

        # first, store the server address - this wouldn't normally be needed,
        # but the tests won't work otherwise (as the DB is _not_ the default one)
        hostname, port = DBMgr._instances[os.getppid()]._db.storage._addr

        DBMgr.setInstance(DBMgr(hostname, port))
        self._dbi = DBMgr.getInstance()

    def isAlive(self):
        return self.is_alive()

    def _setResult(self, res):
        self._result.value = res

    def getResult(self):
        return self._result.value
