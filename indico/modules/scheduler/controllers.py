import logging
import os
import threading
import thread
import time
import random

from zc.queue import Queue
from MaKaC.common import db
from MaKaC.common.logger import Logger
from ZODB.POSException import ConflictError

from indico.modules import ModuleHolder


SLEEP_INTERVAL = 30 # seconds
TASK_MAX_RETRIES = 10 # Number of times to try to run a task before aborting
CONFLICTERROR_MAX_RETRIES = 10

# AWOL = Absent Without Leave
AWOL_TASKS_CHECK_PROBABILITY = 0.3 # [0.0, 1.0) probability that after a Scheduler tick it will check for AWOL tasks in the runningList the lower the number the lower the number of checks
AWOL_TASKS_THRESHOLD = 6000 # seconds to consider a task AWOL

SLEEP_INTERVAL_IF_TOO_MANY_THREADS = 15 # seconds
MAX_TASKS_PER_BURST = 10 # number of tasks that we will process in Scheduler's main loop before sleeping
_touchesTasksContainersLock = None


# logging setup
from MaKaC.common.Configuration import Config
cfg = Config.getInstance()
logger = logging.getLogger('scheduler')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(os.path.join(cfg.getLogDir(), 'scheduler.log'), 'a')
handler.setFormatter(logging.Formatter('%(asctime)s %(threadName)-10s: %(levelname)-8s %(message)s'))
logger.addHandler(handler)


class Scheduler(object):
    '''Scheduler is a singleton in the sense that inside a process only one of it will be running at a given moment
    but it's not a singleton in the sense that you can call Scheduler.getInstance() from within Indico to add new tasks.

    Scheduler.run() is the main loop and every SLEEP_INTERVAL it will spawn new workers to perform that tasks that are pending.
    '''

    __instance = None

    @classmethod
    def getInstance(cls):
        """returns the singleton instance of Scheduler"""
        if cls.__instance == None:
            cls.__instance = Scheduler()

        return cls.__instance


    def __init__(self):
        global _touchesTasksContainersLock
        _touchesTasksContainersLock = threading.Lock()

        self.dbInstance = db.DBMgr.getInstance()
        self.dbInstance.startRequest()
        self.tasksModule = ModuleHolder().getById('tasks')
        # TODO endRequest

    def _relaunchRunningListItems(self):
        # During startup any item in runningList will have died prematurely (except for AWOL tasks)
        # so we relaunch them.
        self.tasksModule = ModuleHolder().getById('tasks')
        for task in self.tasksModule.getRunningList():
            logger.warning('Task %s found in runningList on startup. Relaunching..' % task.id)
            task.tearDown()
            self.tasksModule.removeTaskFromRunningList(task)
            self.addTask(task)


    def run(self):
        '''Main loop, should only be called from scheduler'''
        global _touchesTasksContainersLock
        logger.debug('scheduler started')

        self._relaunchRunningListItems()
        i = 0
        while True:
            returned_tasks_ids = []
            self._readFromDb()
            # The following line is just to make sure that we are getting the updated tasks holder
            self.tasksModule = ModuleHolder().getById('tasks')
            _touchesTasksContainersLock.acquire()
            curTask = self.tasksModule.getNextWaitingTask()
            _touchesTasksContainersLock.release()
            logger.debug('Status: waitingList: [%d] | runningList: [%d]' % (len(self.tasksModule.getWaitingQueue()), len(self.tasksModule.getRunningList())))
            if i >= MAX_TASKS_PER_BURST:
                logger.debug('Too many tasks done in a burst. Sleeping for %d secs..' % SLEEP_INTERVAL)
                time.sleep(SLEEP_INTERVAL)
                i = 0
            elif not curTask:
                logger.debug('Nothing to do. Sleeping for %d secs..' % SLEEP_INTERVAL)
                time.sleep(SLEEP_INTERVAL)
            else:
                i += 1
                # The task has a startOn date in the future and we have already seen
                # the task this round
                if curTask.id in returned_tasks_ids:
                    Scheduler.addTask(curTask)
                    logger.debug('Only future tasks in the incomingQueue. Sleeping for %d secs..' % SLEEP_INTERVAL)
                    time.sleep(SLEEP_INTERVAL)

                # the task starts in the future and we have not seen it yet
                elif curTask.getStartOn() and curTask.getStartOn() > time.time():
                    Scheduler.addTask(curTask)
                    returned_tasks_ids.append(curTask.id)

                # The task is periodicUnique and it is already in the runningList
                elif curTask.isPeriodicUnique() and curTask.__class__ in [x.__class__ for x in self.tasksModule.getRunningList()]:
                    logger.warning('PeriodicUniqueTask %s is already running, ignoring this element from the queue..' % curTask.id)
                    continue

                # Everything else
                else:
                    curTask.setOnRunningListSince(time.time())
                    # logger.warning('%s.getOnRunningListSince(): %s' % (curTask.id, curTask.getOnRunningListSince()))
                    self._writeToDb()

                    self.tasksModule.addTaskToRunningList(curTask)
                    tooManyThreads = True
                    while tooManyThreads:
                        try:
                            Worker(curTask).start()
                        except thread.error:
                            time.sleep(SLEEP_INTERVAL_IF_TOO_MANY_THREADS)
                            logger.warning('Too many open threads, sleeping for %d secs' % SLEEP_INTERVAL_IF_TOO_MANY_THREADS)
                        else:
                            tooManyThreads = False

            # we check AWOL tasks from time to time
            if random.random() < AWOL_TASKS_CHECK_PROBABILITY:
                self._checkAWOLTasks()


    def _writeToDb(self):
        # logger.debug('_writeToDb()..')
        ok = False
        for i in range(CONFLICTERROR_MAX_RETRIES):
            try:
                self.dbInstance.commit()
            except ConflictError:
                self._readFromDb() # TODO seguro?
                pass
            else:
                ok = True
                break

        if not ok:
              logger.error('_writeToDb failed for %d times. Something bad must be going on..' % CONFLICTERROR_MAX_RETRIES)


    def _readFromDb(self):
        # logger.debug('_readFromDb()..')
        self.dbInstance.sync()


    def touchesTasksContainers(func):
        '''This wrapper will make sure that the method it wraps around will
           not be interleaved with another method call that also touches tasks
           containers.

           It is used to make sure accesses to incomingQueue and runningList
           are serial'''
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
        def _commitAfterwards(*args, **kwds):
            retval = func(*args)
            args[0]._p_changed = 1 # args[0] is self(SchedulerModule)

            #root = db.DBMgr.getInstance().getDBConnection().root()
            #root["tasksIncomingQueue"] = args[0].waitingQueue
            try:
                db.DBMgr.getInstance().commit()
            except ConflictError, e:
                logging.getLogger('scheduler').debug('db commitAfterwards ConflictError. Syncync and retrying..')
                db.DBMgr.getInstance().sync()
                db.DBMgr.getInstance().commit()

            logging.getLogger('scheduler').debug('db Commit()')
            return retval

        return _commitAfterwards



    @commitAfterwards
    @touchesTasksContainers
    def _checkAWOLTasks(self):
        for task in self.tasksModule.getRunningList():
            if not task.getOnRunningListSince():
                logger.warning('Task %s is in the runningList but has no onRunningListSince value! Removing from runningList' % (task.id))
                task.tearDown()
                self.tasksModule.removeTaskFromRunningList(task)
            else:
                runForSecs = time.time() - task.getOnRunningListSince()
                if runForSecs > AWOL_TASKS_THRESHOLD:
                    logger.warning('Task %s has been running for %d secs. Assuming it has died abnormally and forcibly calling its tearDown()..' % (task.id, runForSecs))
                    task.tearDown()
                    self.tasksModule.removeTaskFromRunningList(task)


    @commitAfterwards
    @touchesTasksContainers
    def notifyTaskFinished(self, task):
        '''Called by a task when it's done. If a task doesn't notify us
        after AWOL_TASKS_THRESHOLD seconds we assume she went AWOL and we notify admins'''
        logger.debug('Task %s says she\'s finished..' % (task.id))

        if self.tasksModule.removeTaskFromRunningList(task): # if the wask on the running list
            task.tearDown()


    def notifyTaskFinishedAbruptly(self, task):
        self.notifyTaskFinished(task)
        # TODO send email to admins


    # The following methods are the interface for operating with tasks _outside_ of the Scheduler main loop
    # They assume a working db connection and requent commit handling

    @classmethod
    def addTask(self, task):
        '''Submits a new task'''
        # self._readFromDb()
        ModuleHolder().getById('tasks').addTaskToWaitingQueue(task)


class Worker(threading.Thread):
    def __init__(self, task):
        super(Worker, self).__init__()
        self.task = task
        logger = logging.getLogger('scheduler')


    def run(self):
        logger.debug('Running task %s..' % self.task.id)
        # We will try to run the task TASK_MAX_RETRIES times and if it continues failing we abort it
        i = 0
        while i < TASK_MAX_RETRIES and not self.task.endedOn:
            i = i + 1
            try:
                # self.task.reset()
                self.task.start()
            except Exception, e:
                nextRunIn = i * 10 # secs
                logger.warning('Task %s failed with exception %s. Retrying for the %dth time in %d secs..' % (self.task.id, e, i + 1, nextRunIn))
                # We sleep progressivelly so that if the error is caused by concurrency
                # we don't make the problem worse by hammering the server.
                time.sleep(nextRunIn)
            else:
                break
        # db.DBMgr.getInstance().endRequest()
        # db.DBMgr.getInstance().startRequest()
        if self.task.endedOn: # task successfully finished
            Scheduler.getInstance().notifyTaskFinished(self.task)
            if i > 1:
                logger.warning('Task %s failed %d times before finishing correctly' % (self.task.id, i - 1))
        else:
            logger.error('Task %s failed too many (%d) times. Aborting its execution..' % (self.task.id, i))
            Scheduler.getInstance().notifyTaskFinishedAbruptly(self.task)
