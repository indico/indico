import logging
import time
from datetime import timedelta

import ZODB
from persistent import Persistent

from controllers import Supervisor

class BaseTask(Persistent):
    '''To create a new Task subclass Task and define a _run() method with the tasks' actions
    Description of each attribute:
    AUTOMATIC ATTRS:
    - startedOn:  actual date the task started running
    - endedOn:    actual date the task's run method finished
    - running:    True or False depending on what the task thinks it's happening
    
    USER-CONFIGURABLE ATTRS (through kw arguments to init and setters/getters)
    - startOn:    time at which the task creator wanted the task to start (can be blank)
    - endOn:      last point in time where the task can run. A task will never enter the 
                  runningQueue if current time is past endOn
    '''
    def __init__(self, **kwargs):
        self.id = self.__class__.__name__
        self.reset(**kwargs)


    def reset(self, **kwargs):
        '''Resets a task to its state before being run'''
        self.startedOn = None
        self.endedOn = None
        self.running = False
        self.onRunningListSince = None
        self.startOn = None
        self.endOn = None
        
        for k in ('startOn', 'endOn'):
            if k in kwargs:
                setattr(self, k, kwargs[k])
                
        logging.getLogger('taskDaemon').warning('Task %s reset' % self.id)
    
    def getEndOn(self):
        return self.EndOn
    
    def getStartOn(self):
        return self.startOn
    
    def setStartOn(self, newtime):
        self.startOn = newtime
    
    def setEndOn(self, newtime):
        self.endOn = newtime
        
    def setOnRunningListSince(self, sometime):
        self.onRunningListSince = sometime
        self._p_changed = 1
        
        
    def getOnRunningListSince(self):
        return self.onRunningListSince
    
    def getId(self):
        return self.id
    
    def setId(self, newid):
        self.id = newid
    
    def isPeriodic(self):
        return False
    
    def isPeriodicUnique(self):
        return False
    
    def getStartedOn(self):
        return self.startedOn
    
    def getEndedOn(self):
        return self.endedOn
    
    def start(self):
        if self.startOn and time.time() < self.startOn:
            logging.getLogger('taskDaemon').debug('Task %s will sleep for some time. Her time has not come yet startOn (%s) > current time (%s)' % (self.id, self.startOn, time.time()))
            time.sleep(time.time() - self.startOn)
            
        if self.endOn and time.time() > self.endOn:
            logging.getLogger('taskDaemon').warning('Task %s will not be executed, endOn (%s) < current time (%s)' % (self.id, self.endOn, time.time()))
            return False
         
        self.startedOn = time.time()
        self.running = True
        self.run()
        self.running = False
        self.endedOn = time.time()
       
    
    def tearDown(self):
        '''If a task needs to do something once it has run and been removed from runningList
        overload this method'''
        pass
        


class OneShotTask(BaseTask):
    '''Tasks that are executed only once'''
    def __init__(self, **kwargs):
        super(OneShotTask, self).__init__(**kwargs)
        if 'runOn' in kwargs:
            self.runOn = kwargs['runOn']
        else:
            self.runOn = time.time()
            
        
    def getRunOn(self):
        return self.runOn
    
    def start(self):
        diff = self.runOn - time.time() 
        if diff < -60: # we only warn if we are over 60 seconds late
            logging.getLogger('taskDaemon').warning('Task %s should have been executed %d ago' % (self.id, -diff))
        else:
            if diff < 0:
                diff = 0
            logging.getLogger('taskDaemon').debug('Sleeping for %d secs before executing OneShotTask %s' % (diff, self.id))
            time.sleep(diff)
            
        super(OneShotTask, self).start()
            

class PeriodicTask(BaseTask):
    '''Tasks that should be executed at regular intervals'''
    
    def __init__(self, **kwargs):
        '''Must be fed:
            - interval: seconds between each successive run
        '''
        super(PeriodicTask, self).__init__(**kwargs)
        if 'interval' not in kwargs:
            raise Exception('Error: PeriodicTask was not given an interval')
        
        self.interval = kwargs['interval']
    
    
    def isPeriodic(self):
        return True
    
    def getInterval(self):
        return self.interval
    
    def start(self):
        super(PeriodicTask, self).start()
        #logging.getLogger('taskDaemon').debug('PeriodicTask %s finished, sleeping %d secs before next run..' % (self.id, (self.interval - timedelta(0, self.endedOn - self.startedOn)).seconds))
        #time.sleep((self.interval - timedelta(0, self.endedOn - self.startedOn)).seconds)
        
    def tearDown(self):
        super(PeriodicTask, self).tearDown()
        # precision of seconds, don't use this for real time response systems
        
        # We reinject ourselves into the Queue
        self.reset()
        Supervisor.addTask(self)
        
        
class PeriodicUniqueTask(PeriodicTask):
    '''Singleton periodic tasks: no two or more PeriodicUniqueTask of this 
    class will be queued or running at the same time''' 
    def __init__(self, **kwargs):
        super(PeriodicUniqueTask, self).__init__(**kwargs)
        
    def isPeriodicUnique(self):
        return True