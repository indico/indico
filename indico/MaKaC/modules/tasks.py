import logging

from zc.queue import Queue

from MaKaC.common import db
import MaKaC.modules.base as modules

class TasksModule(modules.Module):
    id = "tasks"
    
    def __init__(self): 
        # logging.getLogger('taskDaemon') = logging.getLogger('taskDaemon')
        # logging.getLogger('taskDaemon').warning('Creating incomingQueue and runningList..')
        self.waitingQueue = Queue()
        self.runningList = []
        

    def addTaskToWaitingQueue(self, task):
        logging.getLogger('taskDaemon').debug('Added task %s to waitingList..' % task.id)
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
        logging.getLogger('taskDaemon').debug('Added task %s to runningList..' % task.id)
        self.runningList.append(task)
    
    
    def removeTaskFromRunningList(self, task):
        if task in self.runningList:
            self.runningList.remove(task)
            return True
        else:
            logging.getLogger('taskDaemon').warning('task %s (%s) should have been on runningList but it was not found' % (task.id, task))
            return False