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


import logging
import os
import socket

from BTrees.IOBTree import IOBTree
from BTrees.Length import Length

from indico.modules import Module
from indico.modules.scheduler import base
from indico.util.struct.queue import PersistentWaitingQueue
from indico.util.date_time import int_timestamp
from indico.core.index import IOIndex, IIndexableByArbitraryDateTime

from zc.queue import Queue

class SchedulerModule(Module):
    id = "scheduler"

    def __init__(self):
        # logging.getLogger('scheduler') = logging.getLogger('scheduler')
        # logging.getLogger('scheduler').warning('Creating incomingQueue and runningList..')
        self._waitingQueue = PersistentWaitingQueue()
        self._runningList = []

        # Failed tasks (there is an object still in the DB)
        self._failedIndex = IOIndex(IIndexableByArbitraryDateTime)

        # Finished tasks (no object data, just metadata)
        self._finishedIndex = IOIndex(IIndexableByArbitraryDateTime)

        # Stores all tasks
        self._taskIdx = IOBTree()
        self._taskCounter = Length(0)

        # Is the scheduler running
        self._schedulerStatus = False
        self._hostname = None
        self._pid = None

        # Temporary area where all the tasks stay before being
        # added to the waiting list
        self._taskSpool = Queue()

    def _assertTaskStatus(self, task, status):
        """
        Confirm the status of this task
        """

        if task.status != status:
            raise base.TaskInconsistentStatusException(
                "%s status is not %s" %
                (task, base.status(status)))

        if status == base.TASK_STATUS_RUNNING and \
               task not in self._runningList:
                raise base.TaskInconsistentStatusException(
                    'task %s was not found in the running task list' % task)

        # TODO: remaining elifs

    def _indexTask(self, task):
        """
        Provide the task with an id and add it to the
        task index
        """

        # give it a serial id
        task.initialize(self._taskCounter(), base.TASK_STATUS_SPOOLED)

        # index it and increase the count
        self._taskIdx[task.id] = task
        self._taskCounter.change(1)

        logging.getLogger('scheduler').debug(
            'Added %s to index..' % task)


    ## These are all interface methods, called by different modules

    def getStatus(self):
        """
        Returns some basic info
        """

        return {
            'state': self._schedulerStatus,
            'hostname': getattr(self, '_hostname', None),
            'pid': getattr(self, '_pid', None),
            'waiting': len(self._waitingQueue),
            'running': len(self._runningList),
            'spooled': len(self._taskSpool),
            'failed': self._failedIndex._num_objs() ,
            'finished': self._finishedIndex._num_objs()
            }

    def getTaskById(self, taskId):
        return self._taskIdx[taskId]

    def getSpool(self):
        return self._taskSpool

    def clearSpool(self):
        i = 0

        try:
            while(self._taskSpool.pull()):
                i += 1
        except IndexError:
            pass

        return i

    def spool(self, op, obj):
        """
        Adds an 'instruction' to the spool, in the form (op, obj)
        """

        self._taskSpool.put((op, obj))

        logging.getLogger('scheduler').debug(
            'Added instruction %s to spool..' % ((op, obj),))

        return True

    def removeRunningTask(self, task):
        """
        Remove a task from the running list
        """
        try:
            self._runningList.remove(task)
            self._p_changed = True
        except ValueError:
            logging.getLogger('scheduler').exception("Problem removing running task: %s" % self._runningList)

    def moveTask(self, task, moveFrom, status, occurrence=None, nocheck=False):
        """
        Move a task somewhere
        """
        if not occurrence:
            occurrence = task

        if not nocheck:
            self._assertTaskStatus(task, moveFrom)

        if moveFrom == base.TASK_STATUS_RUNNING:
            # actually remove it from list
            self.removeRunningTask(task)

        elif moveFrom == base.TASK_STATUS_QUEUED:
            idx_timestamp = int_timestamp(task.getStartOn())
            self._waitingQueue.dequeue(idx_timestamp, task)
        elif moveFrom == base.TASK_STATUS_FAILED:
            self._failedIndex.unindex_obj(task)

        # index it either in finished or failed
        # (or queue it up again)
        if status == base.TASK_STATUS_FINISHED:
            self._finishedIndex.index_obj(occurrence)
        elif status in [base.TASK_STATUS_FAILED,
                        base.TASK_STATUS_TERMINATED]:
            self._failedIndex.index_obj(occurrence)
        elif status == base.TASK_STATUS_QUEUED:
            self.addTaskToWaitingQueue(occurrence)

    def changeTaskStartDate(self, oldTS, task):

        newTS = int_timestamp(task.getStartOn())

        # enqueue-dequeue
        try:
            self._waitingQueue.dequeue(oldTS, task)
        except:
            logging.getLogger('scheduler').error(
                "%s was supposed to be changed but it was not "
                "found in the waiting queue!" % task)
            return

        self._waitingQueue.enqueue(newTS, task)

        logging.getLogger('scheduler').info(
            '%s moved from bin %s to %s...' % (task, oldTS, newTS))

    def addTaskToWaitingQueue(self, task, index=False):

        if index:
            self._indexTask(task)

        # get an int timestamp
        if task.getStartOn():
            timestamp = int_timestamp(task.getStartOn())

            self._waitingQueue.enqueue(timestamp, task)

            # make it "officially" queued
            task.setStatus(base.TASK_STATUS_QUEUED)

            logging.getLogger('scheduler').debug(
                'Added %s to waitingQueue..' % task)

    def popNextWaitingTask(self):
        return self._waitingQueue.pop()

    def peekNextWaitingTask(self):
        return self._waitingQueue.peek()

    def removeWaitingTask(self, timestamp, task):
        return self._waitingQueue.dequeue(timestamp, task)

    def getRunningList(self):
        return self._runningList

    def getWaitingQueue(self):
        return self._waitingQueue

    def getFailedIndex(self):
        return self._failedIndex

    def getFinishedIndex(self):
        return self._finishedIndex

    def getTaskIndex(self):
        return self._taskIdx

    def setSchedulerRunningStatus(self, status):
        self._schedulerStatus = status
        self._hostname = socket.getfqdn() if status else None
        self._pid = os.getpid() if status else None

    def addTaskToRunningList(self, task):

        logging.getLogger('scheduler').debug(
             'Added task %s to runningList..' % task.id)
        self._runningList.append(task)
        self._p_changed = True

    ## def removeTaskFromQueue(self, task):
    ##     """
    ##     """

    ##     index = None

    ##     self._waitingQueue.dequeue(task)

    ## def removeTask(self, task):
    ##     """
    ##     Remove a task, no matter what is its current state
    ##     """

    ##     # TODO - implement this using task code?

    ##     # Task still running - throw exception
    ##     if task.state  == base.TASK_STATUS_RUNNING:
    ##         raise base.TaskStillRunningException(task)

    ##     # task has failed - remove it from 'failed' index
    ##     elif task.state == base.TASK_STATUS_FAILED:
    ##         self._failedIndex.unindex_doc(task.id)

    ##     # task has finished - remove it from 'finished' index
    ##     elif task.state == base.TASK_STATUS_FINISHED:
    ##         self._finishedIndex.unindex_doc(task.id)

    ##     # task is queued - removed it from queue
    ##     elif task.state == base.TASK_STATUS_QUEUED:
    ##         self.removeTaskFromQueue(task)


    ##     # task not found - throw exception
    ##     else:
    ##         raise base.TaskInconsistentStatusException()

    ## def deleteTask(self, task):
    ##     """
    ##     Add a task to the TrashCanManager.
    ##     No unindexing is done by this method
    ##     """

    ##     self.removeTask(task)

    ##     TrashCanManager().add(task)
