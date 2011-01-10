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

import time

from indico.ext.livesync import SyncManager
from indico.tests.python.unit.util import IndicoTestFeature, IndicoTestCase
from indico.util.date_time import nowutc, int_timestamp


class LiveSync_Feature(IndicoTestFeature):
    _requires = ['plugins.Plugins', 'util.ContextManager']

    def start(self, obj):
        super(LiveSync_Feature, self).start(obj)

        with obj._context('database'):
            obj._ph.getPluginType('livesync').toggleActive()
            obj._do._notify('updateDBStructures', 'indico.ext.livesync',
                            None, None, None)

            obj._sm = SyncManager.getDBInstance()

    def destroy(self, obj):
        super(LiveSync_Feature, self).destroy(obj)


class _TestSynchronization(IndicoTestCase):

    _requires = ['db.DummyUser', LiveSync_Feature, 'util.RequestEnvironment']

    def setUp(self):
        super(_TestSynchronization, self).setUp()

    def tearDown(self):
        super(_TestSynchronization, self).tearDown()
        self._closeEnvironment()

    def _prettyActions(self, asets):

        def friendlyAction(a):
            return (a._obj, ' '.join(sorted(a._actions)))

        return list(set(friendlyAction(a) for a in s) for s in asets)

    def _nextTS(self):
        time.sleep(1)
        return int_timestamp(nowutc())

    def checkActions(self, fromTS, expected):
        self.assertEqual(self._prettyActions(
            list(self._sm.getTrack().values(None, fromTS))), expected)
