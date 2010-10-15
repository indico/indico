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
from indico.modules.scheduler.slave import ProcessWorker, ThreadWorker
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
        # either 'threads' or 'processes'
        'multitask_mode': 'threads',

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

        self._dbi.startRequest()
        self._schedModule = SchedulerModule.getDBInstance()

        self._runningWorkers = {}

    ## DB access - surrounded by commit retry cycle

    @base.OperationManager
    def _db_popFromSpool(self):
        """
        Get the the element at the top of the spool
        """
        spool = self._schedModule.getSpool()

        try:
            pair = spool.pull()
        except IndexError:
            pair = None

        return pair

    @base.OperationManager
    def _db_setRunningStatus(self, value):
        self._schedModule.setSchedulerRunningStatus(value)

    @base.OperationManager
    def _db_moveTask(self, task, moveFrom, status, occurrence = None, nocheck = False):
        self._schedModule.moveTask(task, moveFrom, status,
                                   occurrence = occurrence, nocheck = nocheck)

    @base.OperationManager
    def _db_addTaskToQueue(self, task, index = True):
        """
        Submits a new task
        """
        SchedulerModule.getDBInstance().addTaskToWaitingQueue(task,
                                                              index = index)
        self._logger.info("Task %s queued for execution" % task)

    @base.OperationManager
    def _db_setTaskRunning(self, timestamp, curTask):
        # remove task from waiting list
        self._schedModule.removeWaitingTask(timestamp, curTask)

        # mark the task as being in the running list
        curTask.setOnRunningListSince(self._getCurrentDateTime())

        # add it to the running list
        self._schedModule.addTaskToRunningList(curTask)

    @base.OperationManager
    def _db_notifyTaskStatus(self, task, status):
        """
        Called by a task when it's done. If a task doesn't notify us
        after AWOL_TASKS_THRESHOLD seconds we assume it went AWOL and
        we notify the admins
        """

        if status == base.TASK_STATUS_FINISHED:
            self._logger.info('Task %s says it has finished..' % task)
        elif status == base.TASK_STATUS_FAILED:
            self._logger.error('Task %s says it has failed..' % task)
        else:
            raise Exception('Impossible task state')

            # clean up the mess
            task.tearDown()

        # if it's a periodic task, do some extra things
        if isinstance(task, tasks.PeriodicTask):
            # prepare an "occurrence" object
            occurrence = tasks.TaskOccurrence(task)

            task.addOccurrence(occurrence)

            # if the task is supposed to be run again
            if task.shouldComeBack():

                # reset "ended on"
                task.setEndedOn(None)

                # calculate next occurrence
                task.setNextOccurrence()

                # move the occurrence to the correct place
                self._schedModule.moveTask(task,
                                           base.TASK_STATUS_RUNNING,
                                           status,
                                           occurrence = occurrence)

                # do not index the task again
                self._db_addTaskToQueue(task, index = False)

                self._logger.info('Task %s rescheduled for %s' %
                                  (task, task.getStartOn()))

        else:
            # move the task to the correct place
            self._schedModule.moveTask(task,
                                       base.TASK_STATUS_RUNNING,
                                       status)

        task.setStatus(status)

    ####

    def _getCurrentDateTime(self):
        return base.TimeSource.get().getCurrentTime()

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
                self._db_moveTask(task,
                                  base.TASK_STATUS_RUNNING,
                                  base.TASK_STATUS_QUEUED)
            except base.TaskInconsistentStatusException, e:
                self._logger.exception("Problem relaunching task %s - "
                                       "setting it as failed" % task)
                self._db_moveTask(
                    task,
                    base.TASK_STATUS_RUNNING,
                    base.TASK_STATUS_FAILED,
                    nocheck=True)

                self._dbi.commit();

    def _iterateTasks(self):
        """
        Iterate over all the tasks in the waiting queue, blocking
        in case there are none
        """
        while True:

            currentTimestamp = int_timestamp(self._getCurrentDateTime())

            # this will basically abort the transaction, so, make sure
            # everything important before this was committed
            self._readFromDb()

            # print a status message (only in debug mode)
            self._printStatus(mode = 'debug')

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

            # get the next task in queue
            res = self._schedModule.peekNextWaitingTask()

            if res:
                # it's actually a timestamp, task tuple
                nextTS, nextTask = res

                self._logger.debug((nextTS, currentTimestamp, self._getCurrentDateTime()))

                # if it's time to execute the task
                if  (nextTS <= currentTimestamp):
                    yield nextTS, nextTask

                    # don't sleep, jump back to the beginning of the cycle
                    continue

            # we assume the task cycle has been completed (if there was one)
            # so, we can just reset the db status (sync)
            self._readFromDb()

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

        for taskId, thread in self._runningWorkers.items():

            # the thread is dead? good, it's finished
            if not thread.isAlive():
                task = self._schedModule._taskIdx[taskId]

                # let's check if it was successful or not
                # and write it in the db
                if thread.getResult() == True:
                    self._db_notifyTaskStatus(task, base.TASK_STATUS_FINISHED)
                elif thread.getResult() == False:
                    self._db_notifyTaskStatus(task, base.TASK_STATUS_FAILED)
                else:
                    # something weird happened
                    self._logger.warning("task %s finished, but the return value "
                                         "was %s" %
                                         (task, thread.getResult()))

                # delete the entry from the dictionary
                del self._runningWorkers[taskId]
                thread.join()

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
            self._db_setRunningStatus(True)

            self._logger.info('**** Scheduler started')
            self._printStatus()

            # relaunch items that were running in the last session
            self._relaunchRunningListItems()


            # iterate over the tasks in the waiting queue
            # that should be running
            for timestamp, curTask in self._iterateTasks():
                # execute the "task cycle" for each new task
                self._taskCycle(timestamp, curTask)

        except base.SchedulerQuitException, e:
            self._logger.info('Scheduler was shut down: %s' % e)
            return 0
        except:
            self._logger.exception('Unexpected error')
            raise
        finally:
            self._logger.info('Setting running status as False')

            self._db_setRunningStatus(False)

    def _taskCycle(self, timestamp, curTask):

        self._db_setTaskRunning(timestamp, curTask)

        # Start a worker subprocess
        # Add it to the thread dict

        if self._config.multitask_mode == 'processes':
            wclass = ProcessWorker
        else:
            wclass = ThreadWorker
        self._runningWorkers[curTask.id] = wclass(curTask.id, self._config)
        self._runningWorkers[curTask.id].start()

    def _processSpool(self):
        """
        Adds all the tasks in the spool to the waiting list
        """
        # pop the first one
        pair = self._db_popFromSpool()

        while pair:
            op, obj = pair

            if op == 'add':
                self._db_addTaskToQueue(obj)
            elif op == 'del':
                self._deleteTaskFromQueue(obj)
            elif op == 'shutdown':
                raise base.SchedulerQuitException(obj)
            else:
                raise base.SchedulerUnknownOperationException(op)
            pair = self._db_popFromSpool()

    def _sleep(self, msg):
        self._logger.debug(msg)
        base.TimeSource.get().sleep(self._config.sleep_interval)

    def _readFromDb(self):
        self._logger.debug('_readFromDb()..')
        self._dbi.sync()

    def _abortDb(self):
        self._logger.debug('_abortDb()..')
        self._dbi.abort()

    def _deleteTaskFromQueue(self, task):
        """
        """

        if isinstance(task, tasks.PeriodicTask):
            # don't let periodic tasks respawn
            task.dontComeBack()
            self._dbi.commit()

        self._db_moveTask(task,
                          base.TASK_STATUS_QUEUED,
                          base.TASK_STATUS_FAILED)

        self._logger.info("Task %s dequeued" % task)


    def _checkAWOLTasks(self):

        self._logger.info('Checking AWOL tasks...')

        for task in self._schedModule.getRunningList():
            if not task.getOnRunningListSince():
                self._logger.warning("Task %s is in the runningList but has no "
                               "onRunningListSince value! Removing from runningList "
                               "and relaunching..." % (task.id))
                task.tearDown()

                # relaunch it
                self._db_moveTask(
                    task,
                    base.TASK_STATUS_RUNNING,
                    base.TASK_STATUS_QUEUED)
            else:
                runForSecs = int_timestamp(self._getCurrentDateTime()) - \
                             int_timestamp(task.getOnRunningListSince())

                if runForSecs > self._config.awol_tasks_thresold:
                    self._logger.warning("Task %s has been running for %d secs. "
                                   "Assuming it has died abnormally and forcibly "
                                   "calling its tearDown()..." % (task.id, runForSecs))
                    task.tearDown()

                    self._db_moveTask(
                        task,
                        base.TASK_STATUS_RUNNING,
                        base.TASK_STATUS_FAIL)
