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

"""
Tests for scheduler base classes
"""
import unittest, threading, multiprocessing
import time
from datetime import timedelta
from dateutil import rrule

from indico.core.db import DBMgr

from indico.util.date_time import nowutc
from indico.modules.scheduler import Scheduler, SchedulerModule, Client, base
from indico.modules.scheduler.tasks import OneShotTask
from indico.modules.scheduler.tasks.periodic import PeriodicTask
from indico.tests.python.unit.util import IndicoTestFeature, IndicoTestCase

terminated = None


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
        self._shutdown()
        with self._context('database'):
            self._smodule.destroyDBInstance()
        super(_TestScheduler, self).tearDown()

    def setUp(self):
        super(_TestScheduler, self).setUp()

        with self._context('database'):
            self._smodule = SchedulerModule.getDBInstance()

        self._sched = SchedulerThread(self._mode)
        self._sched.start()

    def _checkWorkersFinished(self, timeout, value=1):

        global terminated

        timewaited = 0

        for w in self._workers:
            while terminated[w] != value:
                if timewaited < timeout:
                    base.TimeSource.get().sleep(1)
                    timewaited += 1
                else:
                    return False

        # "courtesy seconds" to allow pending info to be processed by scheduler
        base.TimeSource.get().sleep(2)
        return True

    def _startSomeWorkers(self, type_tasks, time_tasks, **kwargs):
        self._workers = {}

        global terminated
        terminated= multiprocessing.Array('i', [0]*len(type_tasks))

        for i in range(0, len(type_tasks)):
            t = type_tasks[i]
            w = Worker(i, t, time_tasks[i], **kwargs)
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
            del status['pid']
            del status['hostname']
            self.assertEqual(expectedStatus, status)

    def testSimpleFinish(self):
        """
        Creating 1 task that will succeed
        """
        self._startSomeWorkers([TestTask],
                               [base.TimeSource.get().getCurrentTime() + \
                                timedelta(seconds=2)])

        self.assertEqual(self._checkWorkersFinished(10),
                         True)

        self._assertStatus({'state': True,
                            'waiting': 0,
                            'running': 0,
                            'spooled': 0,
                            'finished': 1,
                            'failed': 0})

    def testSameTime(self):
        """
        Running several tasks at the same time
        """
        self._startSomeWorkers([TestTask] * 5,
                               [base.TimeSource.get().getCurrentTime() + \
                                timedelta(seconds=2)] * 5)

        self.assertEqual(self._checkWorkersFinished(10),
                         True)

        self._assertStatus({'state': True,
                            'waiting': 0,
                            'running': 0,
                            'spooled': 0,
                            'finished': 5,
                            'failed': 0})

    def testTaskRelocate(self):
        """
        Creating 1 task and relocating it
        """

        self._startSomeWorkers([TestTask],
                               [base.TimeSource.get().getCurrentTime() + \
                                timedelta(seconds=2)])

        base.TimeSource.get().sleep(1)

        with self._context('database', sync=True) as conn:

            # wait to task to be scheduled
            c = Client()
            while True:
                try:
                    conn.sync()
                    t = c.getTask(0)
                    break
                except KeyError:
                    continue

            c.moveTask(t, base.TimeSource.get().getCurrentTime() + timedelta(seconds=2))

        self.assertEqual(self._checkWorkersFinished(5),
                         True)

        self._assertStatus({'state': True,
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

        self._assertStatus({'state': True,
                            'waiting': 0,
                            'running': 0,
                            'spooled': 0,
                            'finished': 2,
                            'failed': 0})

        with self._context('database', sync=True):
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

        self._assertStatus({'state': True,
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

        self._assertStatus({'state': True,
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
                               [rrule.SECONDLY] * 5,
                               bysecond=tuple(seconds))

        # Not all workers will have finished
        self.assertEqual(self._checkWorkersFinished(100, value=3),
                         True)

        self._assertStatus({'state': True,
                            'waiting': 5,
                            'running': 0,
                            'spooled': 0,
                            'finished': 15,
                            'failed': 0})

    def testPeriodicFailTasks(self):
        """
        Creating 1 periodic task that fails every second time
        """

        self._startSomeWorkers([TestPeriodicFailTask],
                               [rrule.SECONDLY],
                               dtstart=base.TimeSource.get().getCurrentTime(),
                               interval=10)

        # All workers will have finished
        self.assertEqual(self._checkWorkersFinished(55, value=4),
                         True)

        self._assertStatus({'state': True,
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
