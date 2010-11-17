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
System tests for indico.ext.livesync

Here, the notification parts of the plugin are tested in a global way.
"""

import unittest


from indico.ext.livesync import SyncManager
from indico.tests.python.unit.util import IndicoTestCase, IndicoTestFeature

class LiveSync_Feature(IndicoTestFeature):
    _requires = ['plugins.Plugins', 'util.ContextManager']

    def start(self, obj):
        super(LiveSync_Feature, self).start(obj)

        obj._ph.getPluginType('livesync').toggleActive()
        obj._do._notify('updateDBStructures', 'indico.ext.livesync', None, None, None)

        obj._sm = SyncManager.getDBInstance()


    def destroy(self, obj):
        super(LiveSync_Feature, self).destroy(obj)


class _TestSynchronization(IndicoTestCase):

    _requires = ['db.DummyUser', LiveSync_Feature, 'util.RequestEnvironment']

    def setUp(self):
        super(_TestSynchronization, self).setUp()

    def tearDown(self):
        super(_TestSynchronization, self).tearDown()


class TestEventSynchronization(_TestSynchronization):

    def testEventCreation(self):
        self._home.newConference(self._dummy)


