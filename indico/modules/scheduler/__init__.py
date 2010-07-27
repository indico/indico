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


import logging, time, datetime

from BTrees.IOBTree import IOBTree
from BTrees.Length import Length

from MaKaC.trashCan import TrashCanManager

from indico.modules import Module
from indico.modules.scheduler.controllers import Scheduler
from indico.modules.scheduler import base
from indico.util.struct.queue import PersistentWaitingQueue
from indico.util.date_time import int_timestamp
from indico.core.index import IntFieldIndex

class SchedulerModule(Module):
    id = "scheduler"

    def __init__(self):
        # logging.getLogger('scheduler') = logging.getLogger('scheduler')
        # logging.getLogger('scheduler').warning('Creating incomingQueue and runningList..')
        self.waitingQueue = PersistentWaitingQueue()
        self.runningList = []

        # Failed tasks (there is an object still in the DB)
        self._failedIndex = IntFieldIndex()

        # Finished tasks (no object data, just metadata)
        self._finishedIndex = IntFieldIndex()

        # Stores metadata
        self._taskIdx = IOBTree()
        self._taskCounter = Length(0)

    def _assertTaskStatus(self, task, status):
        """
        Confirm the status of this task
        """

        if task.status != status:
            raise base.TaskInconsistentStatusException(
                "%s's status is not %s" %
                (task, status))

        if status == base.TASK_STATUS_RUNNING and \
               task not in self.runningList:
                raise base.TaskInconsistentStatusException(
                    'task %s (%s) was not found in the running task list' %
                    (task.id, task))

        # TODO: remaining elifs

    def addTaskToWaitingQueue(self, task):
        logging.getLogger('scheduler').debug(
            'Added task %s to waitingList..' % task.id)

        # get an int timestamp
        timestamp = int_timestamp(task.getStartOn())
        self.waitingQueue.enqueue(timestamp, task)

    def popNextWaitingTask(self):
        return self.waitingQueue.pop()

    def peekNextWaitingTask(self):
        return self.waitingQueue.peek()

    def removeWaitingTask(self, timestamp, task):
        return self.waitingQueue.dequeue(timestamp, task)

    def getRunningList(self):
        return self.runningList

    def getWaitingQueue(self):
        return self.waitingQueue

    def getFailedIndex(self):
        return self._failedIndex

    def getFinishedIndex(self):
        return self._finishedIndex

    def getTaskIndex(self):
        return self._taskIdx

    def indexTask(self, task):

        # give it a serial id
        task.setId(self._taskCounter())

        # index it and increase the count
        self._taskIdx[task.id] = task
        self._taskCounter.change(1)

        logging.getLogger('scheduler').debug(
            'Added %s to index..' % task)


    def addTaskToRunningList(self, task):

        logging.getLogger('scheduler').debug(
            'Added task %s to runningList..' % task.id)
        self.runningList.append(task)
        self._p_changed = 1

    def removeTaskFromQueue(self, task):
        """
        """

        index = None

        self.waitingQueue.dequeue(task)

    def removeTask(self, task):
        """
        Remove a task, no matter what is its current state
        """

        # TODO - implement this using task code?

        # Task still running - throw exception
        if task.state  == base.TASK_STATUS_RUNNING:
            raise base.TaskStillRunningException(task)

        # task has failed - remove it from 'failed' index
        elif task.state == base.TASK_STATUS_FAILED:
            self._failedIndex.unindex_doc(task.id)

        # task has finished - remove it from 'finished' index
        elif task.state == base.TASK_STATUS_FINISHED:
            self._finishedIndex.unindex_doc(task.id)

        # task is queued - removed it from queue
        elif task.state == base.TASK_STATUS_QUEUED:
            self.removeTaskFromQueue(task)


        # task not found - throw exception
        else:
            raise base.TaskInconsistentStatusException()

    def deleteTask(self, task):
        """
        Add a task to the TrashCanManager.
        No unindexing is done by this method
        """

        self.removeTask(task)

        TrashCanManager().add(task)


    def moveTaskFromRunningList(self, task, status, nocheck=False):
        """
        Remove a task from the running list
        """

        if not nocheck:
            self._assertTaskStatus(task, base.TASK_STATUS_RUNNING)

        # generate a timestamp
        timestamp = int(time.mktime(datetime.datetime.now().timetuple()))

        # actually remove it from list
        self.runningList.remove(task)
        self._p_changed = 1

        # index it either in finished or failed
        if status == base.TASK_STATUS_FINISHED:
            self._finishedIndex.index_doc(task.id, timestamp)
        elif status == base.TASK_STATUS_FAILED:
            self._failedIndex.index_doc(task.id, timestamp)
            # or just re-add it to the waiting queue
        elif status == base.TASK_STATUS_QUEUED:
            self.addTaskToWaitingQueue(task)

