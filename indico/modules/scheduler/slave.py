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

import transaction
from ZEO.Exceptions import ClientDisconnected
from ZODB.POSException import ConflictError

from indico.core.db import DBMgr
from MaKaC.common.mail import GenericMailer
from MaKaC.plugins.RoomBooking.default.dalManager import DBConnection, DALManager
from MaKaC.common.info import HelperMaKaCInfo
from indico.modules.scheduler import SchedulerModule, base, TaskDelayed
from indico.modules.scheduler.base import TimeSource
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
        self._delayed = False

        with self._dbi.transaction():
            schedMod = SchedulerModule.getDBInstance()
            self._task = schedMod.getTaskById(self._taskId)

            # open a logging channel
            self._task.plugLogger(self._logger)

        # XXX: potentially conflict-prone
        with self._dbi.transaction(sync=True):
            self._task.prepare()

    def _prepare_retry(self):
        self._dbi.abort()
        self._dbi.sync()
        GenericMailer.flushQueue(False)
        self._task.plugLogger(self._logger)

    def _prepareDB(self):
        self._dbi = DBMgr.getInstance()

    def _process_task(self):
        with self._dbi.transaction():
            with self._app.app_context():
                fossilize.clearCache()
                self._task.start(self._executionDelay)
                transaction.commit()

    def run(self):
        self._prepare()
        self._logger.info('Running task {}.. (delay: {})'.format(self._task.id, self._executionDelay))

        try:
            for i, retry in enumerate(transaction.attempts(self._config.task_max_tries)):
                with retry:
                    self._logger.info('Task attempt #{}'.format(i))
                    if i > 0:
                        self._prepare_retry()
                    try:
                        self._process_task()
                        break
                    except ConflictError:
                        transaction.abort()
                    except ClientDisconnected:
                        self._logger.warning("Retrying for the {}th time in {} secs..".format(i + 1, seconds))
                        transaction.abort()
                        time.sleep(i * 10)
                    except TaskDelayed, e:
                        self._logger.info("{} delayed by {} seconds".format(self._task, e.delaySeconds))
                        self._delayed = True
                        self._executionDelay = 0
                        time.sleep(e.delaySeconds)
            GenericMailer.flushQueue(True)

        except Exception as e:
            self._logger.exception("{} failed with exception '{}'".format(self._task, e))
            transaction.abort()

        finally:
            self._logger.info('{} ended on: {}'.format(self._task, self._task.endedOn))
            # task successfully finished
            if self._task.endedOn:
                with self._dbi.transaction():
                    self._setResult(True)
                if i > (1 + int(self._delayed)):
                    self._logger.warning("{} failed {} times before "
                                         "finishing correctly".format(self._task, i - int(delayed) - 1))
            # task failed
            else:
                with self._dbi.transaction():
                    self._setResult(False)
                self._logger.error("{} failed too many ({}) times. Aborting its execution..".format(self._task, i))
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
