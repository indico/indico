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

import logging
import os
import thread
import time
import random

from MaKaC.common import db
from MaKaC.common.logger import Logger


from indico.modules.scheduler import SchedulerModule, base, tasks
from indico.modules.scheduler.slave import Worker
from indico.util.date_time import nowutc, int_timestamp


class Scheduler(object):
    """
    A :py:class:`~indico.modules.scheduler.Scheduler` object provides a job scheduler
    based on a waiting queue, that communicates with its clients through the database.
    Things have been done in a way that the probability of conflict is minimized, and
    operations are repeated in case one happens.

    The entry point of the process consists of a 'spooler' that periodically takes
    tasks out of a `conflict-safe` FIFO (spool) and adds them to an ``IOBTree``-based
    waiting queue. The waiting queue is then checked periodically for the next task,
    and when the time comes the task is executed.

    Tasks are executed in different threads.

    The :py:class:`~indico.modules.scheduler.Client` class works as a transparent
    remote proxy for this class.
    """

    __instance = None

    # configuration options
    _options = {
        # time to wait between cycles
        'sleep_interval': 10,

        # AWOL = Absent Without Leave
        # [0.0, 1.0) probability that after a Scheduler tick it will check for AWOL
        # tasks in the runningList the lower the number the lower the number of checks
        'awol_tasks_check_probability': 0.3,

        # seconds to consider a task AWOL
        'awol_tasks_thresold': 6000,

        # Number of times to try to run a task before aborting (min 1)
        'task_max_tries': 10
        }

    def __init__(self, **config):
        """
        config is a dictionary containing configuration parameters
        """

        self._readConfig(config)

        self._logger = logging.getLogger('scheduler')

        self._dbi = db.DBMgr.getInstance()
        self._op = base.OperationManager(self._dbi, self._logger)

        self._dbi.startRequest()
        self._schedModule = SchedulerModule.getDBInstance()

        self._runningThreads = {}

    def _readConfig(self, config):
        """
        Reads the config dictionary and verifies the parameters are ok.
        If it's the case, it sets them.
        """

        class DummyType(object):
            pass

        self._config = DummyType()
        self._config.__dict__ = dict(Scheduler._options)

        for name, value in config.iteritems():
            if name not in Scheduler._options:
                raise base.SchedulerConfigurationException(
                    'Option %s is not supported!')
            else:
                setattr(self._config, name, value)

    def _relaunchRunningListItems(self):
        # During startup any item in runningList will have died prematurely
        # (except for AWOL tasks), so we relaunch them.

        for task in self._schedModule.getRunningList():
            self._logger.warning('Task %s found in runningList on startup. Relaunching..' % task.id)
            task.tearDown()
            try:
                self._schedModule.moveTaskFromRunningList(task,
                                                          base.TASK_STATUS_QUEUED)
            except base.TaskInconsistentStatusException, e:
                self._logger.exception("Problem relaunching task %s - "
                                       "setting it as failed" % task)
                self._schedModule.moveTaskFromRunningList(
                    task,
                    base.TASK_STATUS_FAILED,
                    nocheck=True)

                self._dbi.commit();

    def _iterateTasks(self):
        """
        Iterate over all the tasks in the waiting queue, blocking
        in case there are none
        """
        while True:

            currentTimestamp = int_timestamp(nowutc())

            # this will basically abort the transaction, so, make sure
            # everything important before this was committed
            self._readFromDb()

            # print a status message (only in debug mode)
            self._printStatus(mode = 'debug')

            # get the next task in queue
            res = self._schedModule.peekNextWaitingTask()

            if res:
                # it's actually a timestamp, task tuple
                nextTS, nextTask = res

                self._logger.info((nextTS, currentTimestamp))

                # if it's time to execute the task
                if  (nextTS <= currentTimestamp):
                    yield nextTS, nextTask

                    # don't sleep, jump back to the beginning of the cycle
                    continue

            # we assume the task cycle has been completed (if there was one)
            # so, we can just reset the db status (sync)
            self._readFromDb()

            # move the tasks in the spool to the waiting queue
            try:
                self._processSpool()
            finally:
                # this `finally` makes sure finished tasks are handled
                # even if a shutdown order is sent

                # process tasks that have finished meanwhile
                # (tasks have been running in different threads, so, the sync
                # thas was done above won't hurt)
                self._checkFinishedTasks()

            # we also check AWOL tasks from time to time
            if random.random() < self._config.awol_tasks_check_probability:
                self._checkAWOLTasks()

            # if we get here, we have nothing else to do...
            self._sleep('Nothing to do. Sleeping for %d secs...' %
                        self._config.sleep_interval)

    def _checkFinishedTasks(self):
        """
        Check if there are any tasks that have finished recently, and
        need to be moved to the correct places
        """

        self._logger.info("Checking finished tasks")

        for taskId, thread in self._runningThreads.items():

            # the thread is dead? good, it's finished
            if not thread.isAlive():
                task = self._schedModule._taskIdx[taskId]

                # let's check if it was successful or not
                # and write it in the db
                if thread.success:
                    self._notifyTaskFinished(task)
                elif thread.success == False:
                    self._notifyTaskFailed(task)
                else:
                    # something weird happened
                    self._logger.warning("task %s finished, but the return value "
                                         "was %s" %
                                         (task, thread.success))

                # delete the entry from the dictionary
                del self._runningThreads[taskId]

    def _printStatus(self, mode='debug'):
        """
        Print an informative message with some run-time parameters
        """
        status = self._schedModule.getStatus()

        if mode == 'debug':
            func = self._logger.debug
        else:
            func = self._logger.info

        func("Status: waiting: [%(waiting)d] | "
             "running: [%(running)d] | "
             "spooled: [%(spooled)d]" % status)

    def run(self):
        """
        Main loop, should only be called from scheduler
        """

        try:
            self._logger.info('**** Scheduler started')
            self._printStatus()

            # relaunch items that were running in the last session
            with self._op.commit():
                self._relaunchRunningListItems()


            # iterate over the tasks in the waiting queue
            # that should be running
            for timestamp, curTask in self._iterateTasks():
                # execute the "task cycle" for each new task
                self._taskCycle(timestamp, curTask)

        except base.SchedulerQuitException, e:
            self._logger.info('Scheduler was shut down: %s' % e)
            return 0
        except Exception, e:
            self._logger.error('Unexpected error')
            raise e

    def _taskCycle(self, timestamp, curTask):

        # we commit at the end
        with self._op.commit():
            # remove task from waiting list
            self._schedModule.removeWaitingTask(timestamp, curTask)

            # mark the task as being in the running list
            curTask.setOnRunningListSince(nowutc())

            # add it to the running list
            self._schedModule.addTaskToRunningList(curTask)

        # Start a worker subprocess
        # Add it to the thread dict
        self._runningThreads[curTask.id] = Worker(curTask.id, self._config)
        self._runningThreads[curTask.id].start()

    def _popFromSpool(self):
        """
        Get the the element at the top of the spool
        """
        spool = self._schedModule.getSpool()

        try:
            with self._op.commit():
                pair = spool.pull()
        except IndexError:
            pair = None

        return pair

    def _processSpool(self):
        """
        Adds all the tasks in the spool to the waiting list
        """
        # pop the first one
        pair = self._popFromSpool()

        while pair:
            op, obj = pair

            if op == 'add':
                self._addTaskToQueue(obj)
            elif op == 'shutdown':
                raise base.SchedulerQuitException(obj)
            else:
                raise base.SchedulerUnknownOperationException(op)
            pair = self._popFromSpool()

    def _sleep(self, msg):
        self._logger.debug(msg)
        time.sleep(self._config.sleep_interval)

    def _readFromDb(self):
        self._logger.debug('_readFromDb()..')
        self._dbi.sync()

    def _abortDb(self):
        self._logger.debug('_abortDb()..')
        self._dbi.abort()

    def _addTaskToQueue(self, task):
        """
        Submits a new task
        """
        task.setStatus(base.TASK_STATUS_QUEUED)

        with self._op.commit('taskIdx'):
            SchedulerModule.getDBInstance().addTaskToWaitingQueue(task)

        self._logger.info("Task %s queued for execution" % task)


    # notification mechanisms

    def _notifyTaskFinished(self, task):
        """
        """

        # Called by a task when it's done. If a task doesn't notify us
        # after AWOL_TASKS_THRESHOLD seconds we assume it went AWOL and
        # we notify the admins

        self._logger.debug('Task %s says it\'s finished..' % task)

        with self._op.commit():
            self._schedModule.moveTaskFromRunningList(
                task,
                base.TASK_STATUS_FINISHED)
            task.tearDown()

        if isinstance(task, tasks.PeriodicTask):
            with self._op.commit('taskIdx'):
                task.setNextOccurrence()
                SchedulerModule.getDBInstance().addTaskToWaitingQueue(task)

    def _notifyTaskFailed(self, task):

        self._logger.error('Task %s failed..' % task)

        with self._op.commit():
            self._schedModule.moveTaskFromRunningList(
                task,
                base.TASK_STATUS_FAILED)
            task.tearDown()

    def _checkAWOLTasks(self):

        self._logger.info('Checking AWOL tasks...')

        for task in self._schedModule.getRunningList():
            if not task.getOnRunningListSince():
                self._logger.warning("Task %s is in the runningList but has no "
                               "onRunningListSince value! Removing from runningList "
                               "and relaunching..." % (task.id))
                task.tearDown()

                # relaunch it
                with self._op.commit():
                    self._schedModule.moveTaskFromRunningList(
                        task,
                        base.TASK_STATUS_QUEUED)
            else:
                runForSecs = int_timestamp(nowutc()) - \
                             int_timestamp(task.getOnRunningListSince())

                if runForSecs > self._config.awol_tasks_thresold:
                    self._logger.warning("Task %s has been running for %d secs. "
                                   "Assuming it has died abnormally and forcibly "
                                   "calling its tearDown()..." % (task.id, runForSecs))
                    task.tearDown()

                    with self._op.commit():
                        self._schedModule.moveTaskFromRunningList(
                            task,
                            base.TASK_STATUS_FAIL)



