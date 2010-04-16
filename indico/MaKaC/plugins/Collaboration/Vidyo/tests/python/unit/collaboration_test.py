# -*- coding: utf-8 -*-
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

import unittest
from MaKaC.common.db import DBMgr
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.plugins.Collaboration.Vidyo.collaboration import CSBooking
from MaKaC.plugins.Collaboration.Vidyo.tests.python.unit.vidyoTestTools import VidyoTestSetup

def setUpModule():
    DBMgr.getInstance().startRequest()
    VidyoTestSetup.setup()

def tearDownModule():
    DBMgr.getInstance().abort()
    DBMgr.getInstance().endRequest()

class TestCSBookingClass(unittest.TestCase):

    def testObtainVidyoClass(self):
        self.assertEquals(CollaborationTools.getCSBookingClass("Vidyo"),
                          CSBooking)

    def testCreateCSBookingObject(self):
        # we don't bother setting a proper Conference as 2nd argument
        self.assertEquals(type(CollaborationTools.getCSBookingClass("Vidyo")("Vidyo", None)),
                          CSBooking)
