# -*- coding: utf-8 -*-
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

import unittest
from indico.core.db import DBMgr
from MaKaC.plugins.Collaboration.Vidyo.api.client import AdminClient, UserClient
from MaKaC.i18n import _
from MaKaC.plugins.Collaboration.Vidyo.tests.python.unit.vidyoTestTools import VidyoTestSetup

import nose

def setUpModule():
    DBMgr.getInstance().startRequest()
    VidyoTestSetup.setup()

def tearDownModule():
    DBMgr.getInstance().abort()
    DBMgr.getInstance().endRequest()


class TestVidyoConnectivity(unittest.TestCase):

    def testAdminAPIConnectivity(self):
        raise nose.SkipTest
        try:
            AdminClient.getInstance()
        except Exception, e:
            self.fail(msg = "Could not create a Vidyo AdminClient instance. Exception: " + str(e))

    def testUserAPIConnectivity(self):
        raise nose.SkipTest
        try:
            UserClient.getInstance()
        except Exception, e:
            self.fail(msg = "Could not create a Vidyo UserClient instance. Exception: " + str(e))

class TestTypeCreation(unittest.TestCase):
    pass
