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

import unittest, logging
from indico.ext.livesync import PushSyncAgent, ActionWrapper, SyncManager


class ObjectStub(object):
    def __init__(self, oid, name):
        self.id = oid
        self.name = name


class NotificationStub(object):

    def __init__(self, rid, name, actions):
        self.id = rid
        self.name = name
        self.actions = actions


class TestAgent(PushSyncAgent):
    """
    A Test agent is a simple agent used for testing purposes
    """
    def __init__(self, aid, name, description, updateTime, service):
        super(TestAgent, self).__init__(aid, name, description, updateTime)
        self._service = service

    def _generateRecords(self, data, lastTS, dbi=None):

        data = list(data)

        data.reverse()

        return data

    def _run(self, data, logger=None, monitor=None, dbi=None, task=None):

        ts = None

        # send records one by one
        for ts, actions in data:
            for w in actions:
                notf = NotificationStub(w.getObject().id,
                                        w.getObject().name,
                                        w.getActions())
                self._service.inform(notf)

        return ts


class RemoteServiceStub(object):
    """
    Just a test service, simulating some remote server running
    a hypothetical application.
    To make it a bit more user-friendly, our local service (indico) will be a library,
    and remote services different people ("readers") interested on them
    """
    def __init__(self):
        self._records = {}

    def inform(self, notif):
        # we trust the actions will be in the correct order
        # in practice, they should be already ordered

        for action in notif.actions:
            if action == 'del':
                del self._records[notif.id]

            elif action == 'add':
                self._records[notif.id] = (notif.name, 'available')

            elif action == 'chg':
                # since we are using books, let's use states
                # "borrowed" and "available"
                rec = self._records[notif.id]
                state = 'available' if rec[1] == 'borrowed' else 'borrowed'
                self._records[notif.id] = (rec[0], state)

    def getAll(self):
        return set(self._records.itervalues())


class _TestAgentBehavior(unittest.TestCase):

    def _initialize(self):
        self._srvc1 = RemoteServiceStub()
        self._srvc2 = RemoteServiceStub()

        self._mgr = SyncManager(granularity=1)

        # let's create some books
        self._objs = [
            ObjectStub(1, 'Python Cookbook'),
            ObjectStub(2, 'Angels and Demons'),
            ObjectStub(3, 'Der Process')
            ]

class TestPushAgentBehavior(_TestAgentBehavior):

    def setUp(self):

        self._logger = logging.getLogger('')
        self._initialize()

        # agents will act on behalf of the services (readers)
        self._agt1 = TestAgent('testagent1', 'Test Agent 1', 'An agent for testing',
                              1, self._srvc1)
        self._agt2 = TestAgent('testagent2', 'Test Agent 2', 'An agent for testing',
                              1, self._srvc2)

        # Register agents
        self._mgr.registerNewAgent(self._agt1)
        self._mgr.registerNewAgent(self._agt2)

        self._agt1.preActivate(0)
        self._agt2.preActivate(0)
        self._agt1.setActive(True)
        self._agt2.setActive(True)

    def testSimpleRecordCreation(self):
        currentTS = 0
        a1 = ActionWrapper(currentTS, self._objs[1], ['add'], None)
        a2 = ActionWrapper(currentTS, self._objs[2], ['add'], None)

        self._mgr.add(currentTS, [a1, a2])

        currentTS += 1

        # check current available/borrowed books
        self._agt1.run(currentTS, logger=self._logger)
        self._agt1.acknowledge()

        # nice! all of them are available! service should confirm that...
        self.assertEqual(self._srvc1.getAll(),
                         set([('Der Process', 'available'),
                              ('Angels and Demons', 'available')]))

        self.assertEqual(self._srvc2.getAll(),
                         set([]))

        currentTS += 1
        self._agt2.run(currentTS, logger=self._logger)
        self._agt2.acknowledge()

        self.assertEqual(self._srvc2.getAll(),
                         set([('Der Process', 'available'),
                              ('Angels and Demons', 'available')]))

    def testDeletionNotification(self):
        currentTS = 0
        a1 = ActionWrapper(currentTS, self._objs[1], ['add'], None)
        a2 = ActionWrapper(currentTS, self._objs[2], ['add'], None)
        a3 = ActionWrapper(currentTS + 1, self._objs[2], ['del'], None)

        self._mgr.add(currentTS, [a1, a2])

        currentTS += 1
        # check currently available/borrowed books
        self._agt1.run(currentTS, logger=self._logger)
        self._agt1.acknowledge()

        self._mgr.add(currentTS, [a3])

        currentTS += 1
        # check current available/borrowed books
        self._agt2.run(currentTS, logger=self._logger)
        self._agt2.acknowledge()

        self.assertEqual(self._srvc1.getAll(),
                         set([('Der Process', 'available'),
                              ('Angels and Demons', 'available')]))

        self.assertEqual(self._srvc2.getAll(),
                         set([('Angels and Demons', 'available')]))

    def testChangeNotification(self):
        currentTS = 0
        a1 = ActionWrapper(currentTS, self._objs[0], ['add'], None)
        a2 = ActionWrapper(currentTS + 1, self._objs[0], ['chg'], None)
        a3 = ActionWrapper(currentTS + 2, self._objs[0], ['chg'], None)

        self._mgr.add(currentTS, [a1])

        currentTS += 1
        # check current available/borrowed books
        self._agt1.run(currentTS, logger=self._logger)
        self._agt1.acknowledge()

        # srvc2 should be out of sync
        self.assertEqual(self._srvc1.getAll(),
                         set([('Python Cookbook', 'available')]))
        self.assertEqual(self._srvc2.getAll(),
                         set([]))

        # change to borrowed
        self._mgr.add(currentTS, [a2])

        currentTS += 1
        self._agt2.run(currentTS, logger=self._logger)
        self._agt2.acknowledge()

        # srvc1 should be out of sync
        self.assertEqual(self._srvc1.getAll(),
                         set([('Python Cookbook', 'available')]))
        self.assertEqual(self._srvc2.getAll(),
                         set([('Python Cookbook', 'borrowed')]))

        # change back to available
        self._mgr.add(currentTS, [a3])

        currentTS += 1
        self._agt1.run(currentTS, logger=self._logger)
        self._agt1.acknowledge()

        # srvc2 should be out of sync
        self.assertEqual(self._srvc1.getAll(),
                         set([('Python Cookbook', 'available')]))
        self.assertEqual(self._srvc2.getAll(),
                         set([('Python Cookbook', 'borrowed')]))

        currentTS += 1



# TODO: Test PULL
