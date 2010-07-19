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

from zc.queue import Queue

from MaKaC.common import db

from indico.modules import Module
from indico.modules.scheduler.controllers import Scheduler

class SchedulerModule(Module):
    id = "tasks"

    def __init__(self):
        # logging.getLogger('scheduler') = logging.getLogger('scheduler')
        # logging.getLogger('scheduler').warning('Creating incomingQueue and runningList..')
        self.waitingQueue = Queue()
        self.runningList = []


    def addTaskToWaitingQueue(self, task):
        logging.getLogger('scheduler').debug('Added task %s to waitingList..' % task.id)
        self.waitingQueue.put(task)


    def getNextWaitingTask(self):
        try:
            item = self.waitingQueue.pull()
            self.waitingQueue._p_changed = 1
            return item
        except IndexError: # No items in the Queue
            return None


    def getRunningList(self):
        return self.runningList


    def getWaitingQueue(self):
        return self.waitingQueue

    def addTaskToRunningList(self, task):
        logging.getLogger('scheduler').debug('Added task %s to runningList..' % task.id)
        self.runningList.append(task)


    def removeTaskFromRunningList(self, task):
        if task in self.runningList:
            self.runningList.remove(task)
            return True
        else:
            logging.getLogger('scheduler').warning('task %s (%s) should have been on runningList but it was not found' % (task.id, task))
            return False
