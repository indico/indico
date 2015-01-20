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
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.plugins.Collaboration.Vidyo.collaboration import CSBooking
from MaKaC.plugins.Collaboration.Vidyo.tests.python.unit.vidyoTestTools import VidyoTestSetup

from indico.tests.python.unit.util import IndicoTestCase


class TestCSBookingClass(IndicoTestCase):

    _requires = ['plugins.Plugins']

    def testObtainVidyoClass(self):
        with self._context('database'):
            self.assertEquals(CollaborationTools.getCSBookingClass("Vidyo"),
                              CSBooking)

    def testCreateCSBookingObject(self):
        with self._context('database'):
            # we don't bother setting a proper Conference as 2nd argument
            self.assertEquals(type(CollaborationTools.getCSBookingClass("Vidyo")("Vidyo", None)),
                              CSBooking)
