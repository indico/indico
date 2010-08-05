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

"""
Tests for scheduler base classes
"""
import unittest, threading, multiprocessing
import time
from datetime import timedelta
from dateutil import rrule

from MaKaC.common.db import DBMgr

from indico.util.date_time import nowutc
from indico.modules.scheduler import Scheduler, SchedulerModule, Client
from indico.modules.scheduler.tasks import OneShotTask, PeriodicTask

terminated = None


class TestTask(OneShotTask):

    def __init__(self, myid, date_time):
        super(TestTask, self).__init__(date_time)
        self._id = myid

    def run(self):
        time.sleep(1)
        terminated[self._id] = 1


class TestFailTask(TestTask):
    def run(self):
        time.sleep(1)
        terminated[self._id] = 1
        raise Exception('I fail!')


class TestPeriodicTask(PeriodicTask):
    def __init__(self, myid, freq, **kwargs):
        super(TestPeriodicTask, self).__init__(freq, **kwargs)
        self._id = myid

    def run(self):
        terminated[self._id] += 1


class Worker(threading.Thread):

    def __init__(self, myid, task_t, time, **kwargs):
        super(Worker, self).__init__()
        self._id = myid
        self.finished = False
        self._task_t = task_t
        self._time = time
        self._extra_args = kwargs

    def run(self):
        DBMgr.getInstance().startRequest()
        c = Client()
        c.enqueue(self._task_t(self._id, self._time, **self._extra_args))
        DBMgr.getInstance().endRequest()
        pass


class SchedulerThread(threading.Thread):

    def __init__(self, mode):
        super(SchedulerThread, self).__init__()
        self._mode = mode

    def run(self):
        DBMgr.getInstance().startRequest()
        s = Scheduler(sleep_interval = 1,
                      task_max_tries = 1,
                      multitask_mode = self._mode)
        self.result = s.run()
        DBMgr.getInstance().endRequest()


class _TestScheduler(unittest.TestCase):

    def setUp(self):

        DBMgr.getInstance()._conn = {}

        DBMgr.getInstance().startRequest()
        self._smodule = SchedulerModule.getDBInstance()
        DBMgr.getInstance().commit()

        self._sched = SchedulerThread(self._mode)
        self._sched.start()

    def _checkWorkersFinished(self, timeout):

        global terminated

        timewaited = 0

        for w in self._workers:
            while not terminated[w]:
                # timeout at 10 sec
                if timewaited < timeout:
                    time.sleep(1)
                    timewaited += 1
                else:
                    return False
        return True

    def _startSomeWorkers(self, type_tasks, time_tasks, **kwargs):
        self._workers = {}

        global terminated
        terminated= multiprocessing.Array('i',[0]*len(type_tasks))

        for i in range(0, len(type_tasks)):
            w = Worker(i, type_tasks[i], time_tasks[i], **kwargs)
            w.start()
            self._workers[i] = w

        for i in range(0, len(type_tasks)):
            self._workers[i].join()

    def _shutdown(self):
        c = Client()
        c.shutdown()

        DBMgr.getInstance().commit()

        self._sched.join()

    def _assertStatus(self, expectedStatus):
        DBMgr.getInstance().sync()
        status = self._smodule.getStatus()

        self.assertEqual(status, expectedStatus)

    def testSimpleFinish(self):
        """
        Creating 1 tasks that will succeed
        """

        self._startSomeWorkers([TestTask],
                               [nowutc() + timedelta(seconds=2)])
        self.assertEqual(self._checkWorkersFinished(10),
                         True)

        self._shutdown()

        self._assertStatus({'waiting': 0,
                            'running': 0,
                            'spooled': 0,
                            'finished': 1,
                            'failed': 0})

    def testPriority(self):
        """
        Checking that one task is executed before another
        """

        self._workers = {}

        global terminated

        terminated = multiprocessing.Array('i', [0, 0])

        terminated[0] = 0
        terminated[1] = 0

        w1 = Worker(0, TestTask, nowutc() + timedelta(seconds=4))
        w1.start()

        time.sleep(1)

        w2 = Worker(1, TestTask, nowutc() + timedelta(seconds=0))
        w2.start()

        self._workers[0] = w1
        self._workers[1] = w2

        w1.join()
        w2.join()

        self.assertEqual(self._checkWorkersFinished(10),
                         True)

        c = Client()
        c.shutdown()
        DBMgr.getInstance().commit()

        self._sched.join()

        self._assertStatus({'waiting': 0,
                            'running': 0,
                            'spooled': 0,
                            'finished': 2,
                            'failed': 0})


        t1 = c.getTask(0)
        t2 = c.getTask(1)


        self.assertEqual(t1.endedOn > t2.endedOn, True)

    def testSeveralFailFinish(self):
        """
        Creating 10 tasks, 4 of which will fail
        """

        self._startSomeWorkers([TestFailTask for i in range(0, 4)] +
                               [TestTask for i in range(4, 10)],
                               [nowutc() + timedelta(seconds=2)]*10)
        self.assertEqual(self._checkWorkersFinished(10),
                         True)

        self._shutdown()

        self._assertStatus({'waiting': 0,
                            'running': 0,
                            'spooled': 0,
                            'finished': 6,
                            'failed': 4})

    def testSeveralFailFinishWaiting(self):
        """
        Creating 10 tasks, 3 will fail and 2 still be waiting
        """

        self._startSomeWorkers([TestFailTask for i in range(0, 3)] +
                               [TestTask for i in range(3, 10)],
                               [nowutc() + timedelta(seconds=2)]*8 +
                               [nowutc() + timedelta(minutes=200)]*2)

        # Not all workers will have finished
        self.assertEqual(self._checkWorkersFinished(10),
                         False)

        self._shutdown()

        self._assertStatus({'waiting': 2,
                            'running': 0,
                            'spooled': 0,
                            'finished': 5,
                            'failed': 3})


    ## def testPeriodicTasks(self):
    ##     """
    ##     Creating 10 periodic tasks
    ##     """

    ##     self._startSomeWorkers([TestPeriodicTask for i in range(0, 10)],
    ##                            [rrule.MINUTELY] * 10,
    ##                            bysecond = (10,20,30))

    ##     # Not all workers will have finished
    ##     self.assertEqual(self._checkWorkersFinished(40),
    ##                      False)

    ##     self._shutdown()

    ##     self._assertStatus({'waiting': 10,
    ##                         'running': 0,
    ##                         'spooled': 0,
    ##                         'finished': 30,
    ##                         'failed': 3})

 # TODO:
 # some tasks running (test resume)
 # some tasks spooled (test resume)
 # periodic tasks

    def tearDown(self):

        self._smodule.destroyDBInstance()
        DBMgr.getInstance().endRequest()

class TestProcessScheduler(_TestScheduler):
    _mode = 'processes'

class TestThreadScheduler(_TestScheduler):
    _mode = 'threads'
