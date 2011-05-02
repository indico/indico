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
from indico.modules.scheduler import Scheduler, SchedulerModule, Client, base
from indico.modules.scheduler.tasks import OneShotTask, PeriodicTask
from indico.tests.python.unit.util import IndicoTestFeature, IndicoTestCase

terminated = None


class TestTimeSource(base.TimeSource):
    def __init__(self, factor):
        self._startTime = nowutc()
        self._factor = factor

    def getCurrentTime(self):
        realDiff = nowutc() - self._startTime
        seconds = (realDiff.seconds + realDiff.microseconds / 1E6)

        fakeDiff = timedelta(seconds = seconds*self._factor)

        return self._startTime + fakeDiff

    def sleep(self, amount):
        time.sleep(amount/float(self._factor))


class TestTask(OneShotTask):

    def __init__(self, myid, date_time):
        super(TestTask, self).__init__(date_time)
        self._id = myid

    def run(self):
        base.TimeSource.get().sleep(1)
        terminated[self._id] = 1


class TestFailTask(TestTask):
    def run(self):
        base.TimeSource.get().sleep(1)
        terminated[self._id] = 1
        raise Exception('I fail!')


class TestPeriodicTask(PeriodicTask):
    def __init__(self, myid, freq, **kwargs):
        super(TestPeriodicTask, self).__init__(freq, **kwargs)
        self._id = myid

    def run(self):
        terminated[self._id] += 1


class TestPeriodicFailTask(PeriodicTask):
    def __init__(self, myid, freq, **kwargs):
        super(TestPeriodicFailTask, self).__init__(freq, **kwargs)
        self._id = myid

    def run(self):

        terminated[self._id] += 1

        if terminated[self._id] % 2 == 0:
            raise Exception('I fail! %s' % terminated[self._id])


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

        s = Scheduler(sleep_interval=1,
                      task_max_tries=1,
                      multitask_mode=self._mode)
        self.result = s.run()


class _TestScheduler(IndicoTestCase):

    _requires = ['db.DummyUser']

    def tearDown(self):
        with self._context('database'):
            self._smodule.destroyDBInstance()
        super(_TestScheduler, self).tearDown()

    def setUp(self):
        super(_TestScheduler, self).setUp()

        base.TimeSource.set(TestTimeSource(2))

        with self._context('database'):
            self._smodule = SchedulerModule.getDBInstance()

        self._sched = SchedulerThread(self._mode)
        self._sched.start()

    def _checkWorkersFinished(self, timeout, value=1):

        global terminated

        timewaited = 0

        for w in self._workers:
            while terminated[w] != value:
                # timeout at 10 sec
                if timewaited < timeout:
                    base.TimeSource.get().sleep(1)
                    timewaited += 1
                else:
                    ## print "bad news... timeout @ %s, value=%s" % \
                    ##        (w, terminated[w])
                    return False
        return True

    def _startSomeWorkers(self, type_tasks, time_tasks, **kwargs):
        self._workers = {}

        global terminated
        terminated= multiprocessing.Array('i', [0]*len(type_tasks))

        for i in range(0, len(type_tasks)):
            w = Worker(i, type_tasks[i], time_tasks[i], **kwargs)
            w.start()
            self._workers[i] = w

        for i in range(0, len(type_tasks)):
            self._workers[i].join()

    def _shutdown(self):

        with self._context('database', sync=True):
            c = Client()
            c.shutdown()

        self._sched.join()

    def _assertStatus(self, expectedStatus):
        with self._context('database'):
            status = self._smodule.getStatus()
            self.assertEqual(expectedStatus, status)

    def testSimpleFinish(self):
        """
        Creating 1 tasks that will succeed
        """

        self._startSomeWorkers([TestTask],
                               [base.TimeSource.get().getCurrentTime() + \
                                timedelta(seconds=2)])
        self.assertEqual(self._checkWorkersFinished(10),
                         True)

        self._shutdown()

        self._assertStatus({'state': False,
                            'waiting': 0,
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

        w1 = Worker(0, TestTask, base.TimeSource.get().getCurrentTime() + \
                    timedelta(seconds=4))
        w1.start()

        base.TimeSource.get().sleep(1)

        w2 = Worker(1, TestTask, base.TimeSource.get().getCurrentTime() + \
                    timedelta(seconds=0))
        w2.start()

        self._workers[0] = w1
        self._workers[1] = w2

        w1.join()
        w2.join()

        self.assertEqual(self._checkWorkersFinished(10),
                         True)

        self._shutdown()

        self._sched.join()

        self._assertStatus({'state': False,
                            'waiting': 0,
                            'running': 0,
                            'spooled': 0,
                            'finished': 2,
                            'failed': 0})

        with self._context('database'):
            c = Client()
            t1 = c.getTask(0)
            t2 = c.getTask(1)

            self.assertEqual(t1.endedOn > t2.endedOn, True)

    def testSeveralFailFinish(self):
        """
        Creating 5 tasks, 2 of which will fail
        """

        self._startSomeWorkers([TestFailTask] * 2 +
                               [TestTask] * 3,
                               [base.TimeSource.get().getCurrentTime() + \
                                timedelta(seconds=2)]*5)
        self.assertEqual(self._checkWorkersFinished(10),
                         True)

        self._shutdown()

        self._assertStatus({'state': False,
                            'waiting': 0,
                            'running': 0,
                            'spooled': 0,
                            'finished': 3,
                            'failed': 2})

    def testSeveralFailFinishWaiting(self):
        """
        Creating 5 tasks, 2 will fail and 2 still be waiting
        """

        self._startSomeWorkers([TestFailTask] * 2 +
                               [TestTask] * 3,
                               [base.TimeSource.get().getCurrentTime() + \
                                timedelta(seconds=2)] * 3 +
                               [base.TimeSource.get().getCurrentTime() + \
                                timedelta(minutes=200)] * 2)

        # Not all workers will have finished
        self.assertEqual(self._checkWorkersFinished(30),
                         False)

        self._shutdown()

        self._assertStatus({'state': False,
                            'waiting': 2,
                            'running': 0,
                            'spooled': 0,
                            'finished': 1,
                            'failed': 2})

    def testPeriodicTasks(self):
        """
        Creating 5 periodic tasks
        """

        now = base.TimeSource.get().getCurrentTime()

        s = ((now.second / 10) + 1) % 6

        seconds = [s * 10]

        # get intervals of 10 seconds
        for i in range(0, 2):
            s = s + 1
            seconds.append((s % 6) * 10)

        self._startSomeWorkers([TestPeriodicTask] * 5,
                               [rrule.MINUTELY] * 5,
                               bysecond=tuple(seconds))

        # Not all workers will have finished
        self.assertEqual(self._checkWorkersFinished(100, value=3),
                         True)

        self._shutdown()

        self._assertStatus({'state': False,
                            'waiting': 5,
                            'running': 0,
                            'spooled': 0,
                            'finished': 15,
                            'failed': 0})

    def testPeriodicFailTasks(self):
        """
        Creating 1 periodic task that fails every second time
        """

        now = base.TimeSource.get().getCurrentTime()

        s = ((now.second / 10) + 1) % 6

        seconds = [s * 10]

        # get intervals of 10 seconds
        for i in range(0, 3):
            s = s + 1
            seconds.append((s % 6) * 10)

        self._startSomeWorkers([TestPeriodicFailTask],
                               [rrule.MINUTELY],
                               bysecond=tuple(seconds))

        # All workers will have finished
        self.assertEqual(self._checkWorkersFinished(60, value=4),
                         True)

        self._shutdown()

        self._assertStatus({'state': False,
                            'waiting': 1,
                            'running': 0,
                            'spooled': 0,
                            'finished': 2,
                            'failed': 2})

 # TODO:
 # some tasks running (test resume)
 # some tasks spooled (test resume)


class TestProcessScheduler(_TestScheduler):
    _mode = 'processes'


#class TestThreadScheduler(_TestScheduler):
#    _mode = 'threads'
