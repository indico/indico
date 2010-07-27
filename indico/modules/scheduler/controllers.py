import logging
import os
import thread
import time
import random

from MaKaC.common import db
from MaKaC.common.logger import Logger
from ZODB.POSException import ConflictError

from indico.modules import ModuleHolder
from indico.modules.scheduler import base
from indico.util.date_time import nowutc, int_timestamp

# threading vs. multiprocessing
MT_MODE = 'THREAD'

if MT_MODE == 'THREAD':
    import threading
    _MT_MODULE = threading
    _MT_UNIT = threading.Thread
elif SPAWNING_MODE == 'PROCESS':
    import multiprocessing
    _MT_MODULE = multiprocessing
    _MT_UNIT = multiprocessing.Process

###

# some basic definitions
SLEEP_INTERVAL = 10 # seconds
TASK_MAX_RETRIES = 10 # Number of times to try to run a task before aborting
CONFLICTERROR_MAX_RETRIES = 10

# AWOL = Absent Without Leave
AWOL_TASKS_CHECK_PROBABILITY = 0.3 # [0.0, 1.0) probability that after a Scheduler tick it will check for AWOL tasks in the runningList the lower the number the lower the number of checks
AWOL_TASKS_THRESHOLD = 6000 # seconds to consider a task AWOL

SLEEP_INTERVAL_IF_TOO_MANY_THREADS = 15 # seconds
MAX_TASKS_PER_BURST = 10 # number of tasks that we will process in Scheduler's main loop before sleeping
_touchesTasksContainersLock = None

logger = logging.getLogger('scheduler')

def touchesTasksContainers(func):
    """
    This wrapper will make sure that the method it wraps around will
    not be interleaved with another method call that also touches tasks
    containers.

    It is used to make sure accesses to incomingQueue and runningList
    are serial
    """

    def _touchesTasksContainers(*args, **kwds):
        global _touchesTasksContainersLock
        _touchesTasksContainersLock.acquire()
        retval = None
        try:
            retval = func(*args)
        finally:
            _touchesTasksContainersLock.release()

        return retval

    return _touchesTasksContainers


def commitAfterwards(func):
    def _commitAfterwards(self, *args, **kwds):
        retval = func(self, *args)
        self._p_changed = 1

        try:
            db.DBMgr.getInstance().commit()
        except ConflictError, e:
            logger.debug('db commitAfterwards ConflictError. Syncync and retrying..')
            db.DBMgr.getInstance().sync()
            db.DBMgr.getInstance().commit()

        logger.debug('db Commit()')
        return retval

    return _commitAfterwards


class Scheduler(object):
    """
    Scheduler is a singleton in the sense that inside a process only one of it will be running at a given moment
    but it's not a singleton in the sense that you can call Scheduler.getInstance() from within Indico to add new tasks.

    Scheduler.run() is the main loop and every SLEEP_INTERVAL it will spawn new workers to perform that tasks that are pending.
    """

    __instance = None

    @classmethod
    def getInstance(cls):
        """returns the singleton instance of Scheduler"""
        if cls.__instance == None:
            cls.__instance = Scheduler()

        return cls.__instance


    def __init__(self):
        global _touchesTasksContainersLock
        _touchesTasksContainersLock = _MT_MODULE.Lock()

        self.dbInstance = db.DBMgr.getInstance()

        self.dbInstance.startRequest()
        self.tasksModule = ModuleHolder().getById('scheduler')


    def _relaunchRunningListItems(self):
        # During startup any item in runningList will have died prematurely
        # (except for AWOL tasks), so we relaunch them.

        self.tasksModule = ModuleHolder().getById('scheduler')
        for task in self.tasksModule.getRunningList():
            logger.warning('Task %s found in runningList on startup. Relaunching..' % task.id)
            task.tearDown()
            try:
                self.tasksModule.moveTaskFromRunningList(task, base.TASK_STATUS_QUEUED)
            except base.TaskInconsistentStatusException, e:
                logger.exception('Problem relaunching task %s - setting it as failed' % task)
                self.tasksModule.moveTaskFromRunningList(task,
                                                         base.TASK_STATUS_FAILED,
                                                         nocheck=True)
                self.dbInstance.commit();

            self._addTaskToQueue(task)

    def _iterateTasks(self):

        while True:

            # we check AWOL tasks from time to time
            if random.random() < AWOL_TASKS_CHECK_PROBABILITY:
                self._checkAWOLTasks()

            currentTimestamp = int_timestamp(nowutc())

            self._readFromDb()

            logger.debug('Status: waitingList: [%d] | runningList: [%d]' %
                         (len(self.tasksModule.getWaitingQueue()),
                          len(self.tasksModule.getRunningList())))

            res = self.tasksModule.peekNextWaitingTask()

            if res:
                nextTS, nextTask = res

                if  (nextTS <= currentTimestamp):
                    # return something
                    yield nextTS, nextTask

                    # don't sleep
                    continue

            self._sleep('Nothing to do. Sleeping for %d secs...' % SLEEP_INTERVAL)


    def run(self):
        """
        Main loop, should only be called from scheduler
        """

        global _touchesTasksContainersLock
        logger.debug('scheduler started')

        self._relaunchRunningListItems()

        for timestamp, curTask in self._iterateTasks():

            logger.debug("%s %s" % (curTask, curTask.getStartOn()))
            self._taskCycle(timestamp, curTask)


    def _taskCycle(self, timestamp, curTask):

        if nowutc() >= curTask.getStartOn():

            global _touchesTasksContainersLock

            # lock task containers
            with _touchesTasksContainersLock:
                # remove task from waiting list
                self.tasksModule.removeWaitingTask(timestamp, curTask)

                logger.warning('%s > %s' %
                               (curTask.getStartOn(), nowutc()))

                curTask.setOnRunningListSince(nowutc())
                logger.warning('%s.getOnRunningListSince(): %s' %
                               (curTask.id, curTask.getOnRunningListSince()))

                self.tasksModule.addTaskToRunningList(curTask)
                self._writeToDb()

            # Start a worker subprocess
            Worker(curTask).start()
        else:
            self._sleep('Only future tasks in the incomingQueue. '
                        'Sleeping for %d secs..' % SLEEP_INTERVAL)

    def _sleep(self, msg):
        logger.debug(msg)
        time.sleep(SLEEP_INTERVAL)

    def _writeToDb(self):
        # logger.debug('_writeToDb()..')
        ok = False
        for i in range(CONFLICTERROR_MAX_RETRIES):
            try:
                self.dbInstance.commit()
            except ConflictError:
                self._readFromDb()
                pass
            else:
                ok = True
                break

        if not ok:
              logger.error('_writeToDb failed for %d times. Something bad must be going on..' % CONFLICTERROR_MAX_RETRIES)


    def _readFromDb(self):
        logger.debug('_readFromDb()..')
        self.dbInstance.sync()

    def _abortDb(self):
        logger.debug('_abortDb()..')
        self.dbInstance.abort()

    @commitAfterwards
    @touchesTasksContainers
    def _checkAWOLTasks(self):

        logger.info('Checking AWOL tasks')

        for task in self.tasksModule.getRunningList():
            if not task.getOnRunningListSince():
                logger.warning('Task %s is in the runningList but has no onRunningListSince value! Removing from runningList and relaunching' % (task.id))
                task.tearDown()
                # relaunch it
                self.tasksModule.moveTaskFromRunningList(task, base.TASK_STATUS_QUEUED)
            else:
                runForSecs = int_timestamp(nowutc()) - int_timestamp(task.getOnRunningListSince())
                if runForSecs > AWOL_TASKS_THRESHOLD:
                    logger.warning('Task %s has been running for %d secs. Assuming it has died abnormally and forcibly calling its tearDown()..' % (task.id, runForSecs))
                    task.tearDown()
                    self.tasksModule.moveTaskFromRunningList(task, base.TASK_STATUS_FAIL)


    # The following methods are the interface for operating with tasks
    # _outside_ of the Scheduler main loop
    # They assume a working db connection and request commit handling

    @classmethod
    def enqueue(self, task):
        """
        Submits a new task, indexing it
        """
        ModuleHolder().getById('scheduler').indexTask(task)
        self._addTaskToQueue(task)


    @classmethod
    def _addTaskToQueue(self, task):
        """
        Submits a new task
        """
        # self._readFromDb()
        task.status = base.TASK_STATUS_QUEUED
        ModuleHolder().getById('scheduler').addTaskToWaitingQueue(task)

    @classmethod
    def dequeue(self, task):
        """
        Removes a task from the queue
        """
        # self._readFromDb()
        ModuleHolder().getById('scheduler').removeTaskFromQueue(task)


class Worker(_MT_UNIT):

    def __init__(self, task):
        super(Worker, self).__init__()
        self.task = task

        self.tasksModule = ModuleHolder().getById('scheduler')
        self.logger = logging.getLogger('worker')

        # open a logging channel
        self.task.plugLogger(self.logger)

    @commitAfterwards
    @touchesTasksContainers
    def notifyTaskFinished(self, task):
        """
        Called by a task when it's done. If a task doesn't notify us
        after AWOL_TASKS_THRESHOLD seconds we assume she went AWOL and we notify admins
        """

        self.logger.debug('Task %s says it\'s finished..' % task)

        # if task was in the running list
        if self.tasksModule.moveTaskFromRunningList(task, base.TASK_STATUS_FINISHED):
            task.tearDown()

            # Add periodic tasks back to the queue
            if isinstance(task, base.PeriodicTask):
                Scheduler.addTask(self)

    def notifyTaskFinishedAbruptly(self, task):
        self.notifyTaskFinished(task)
        # TODO send email to admins

    def run(self):
        self.logger.debug('Running task %s..' % self.task.id)
        # We will try to run the task TASK_MAX_RETRIES times and if it continues failing we abort it
        i = 0

        dbi = db.DBMgr()

        dbi.startRequest()

        self.logger.debug('db started %s %s' % (self.task, self.task.endedOn))

        while i < TASK_MAX_RETRIES and not self.task.endedOn:
            i = i + 1
            try:
                # self.task.reset()
                self.task.start()

            except Exception, e:
                nextRunIn = i * 10 # secs
                self.logger.warning("Task %s failed with exception '%s'. Retrying for the %dth time in %d secs.." % (self.task.id, e, i + 1, nextRunIn))
                self.logger.exception('Error message')
                # We sleep progressivelly so that if the error is caused by concurrency
                # we don't make the problem worse by hammering the server.
                time.sleep(nextRunIn)
            else:
                break

        self.logger.info('Ended on: %s' % self.task.endedOn)

        if self.task.endedOn: # task successfully finished
            self.notifyTaskFinished(self.task)
            if i > 1:
                self.logger.warning('Task %s failed %d times before finishing correctly' % (self.task.id, i - 1))
        else:
            self.logger.error('Task %s failed too many (%d) times. Aborting its execution..' % (self.task.id, i))
            self.notifyTaskFinishedAbruptly(self.task)

        dbi.endRequest()

