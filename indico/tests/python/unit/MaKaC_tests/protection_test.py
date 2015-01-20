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

import os
from datetime import datetime
from pytz import timezone

from MaKaC.conference import ConferenceHolder
from MaKaC import conference
from indico.tests.python.unit.util import IndicoTestCase, with_context


class TestProtection(IndicoTestCase):

    _requires = ['db.Database', 'db.DummyUser']

    def setUp(self):
        super(TestProtection, self).setUp()

        with self._context("database"):
            # Create a conference
            category = conference.CategoryManager().getById('0')
            self._conf = category.newConference(self._dummy)
            self._conf.setTimezone('UTC')
            sd = datetime(2011, 11, 1, 10, 0, tzinfo=timezone('UTC'))
            ed = datetime(2011, 11, 1, 18, 0, tzinfo=timezone('UTC'))
            self._conf.setDates(sd, ed)
            ch = ConferenceHolder()
            ch.add(self._conf)

            self._contrib1 = conference.Contribution()
            self._conf.addContribution(self._contrib1)

            self._session1 = conference.Session()
            self._conf.addSession(self._session1)

            self._session2 = conference.Session()
            self._conf.addSession(self._session2)

            self._contrib2 = conference.Contribution()
            self._session1.addContribution(self._contrib2)

            #Now we create the material (id=0) and attach it to the contrib
            self._material = conference.Material()
            self._contrib1.addMaterial( self._material )
            #Now we create a dummy file and attach it to the material
            filePath = os.path.join( os.getcwd(), "test.txt" )
            fh = open(filePath, "w")
            fh.write("hola")
            fh.close()
            self._resource = conference.LocalFile()
            self._resource.setFilePath( filePath )
            self._resource.setFileName( "test.txt" )
            self._material.addResource( self._resource )

    @with_context('database')
    def testOnlyPublic(self):
        self.assertEqual(self._conf.getAccessController().isFullyPublic(), True)
        self.assertEqual(self._contrib1.getAccessController().isFullyPublic(), True)
        self.assertEqual(self._contrib2.getAccessController().isFullyPublic(), True)
        self.assertEqual(self._session1.getAccessController().isFullyPublic(), True)
        self.assertEqual(self._session2.getAccessController().isFullyPublic(), True)
        self.assertEqual(self._material.getAccessController().isFullyPublic(), True)
        self.assertEqual(self._resource.getAccessController().isFullyPublic(), True)

    @with_context('database')
    def testOnlyPrivate(self):
        self._conf.setProtection(1)
        self._contrib1.setProtection(1)
        self._contrib2.setProtection(1)
        self._session1.setProtection(1)
        self._session2.setProtection(1)
        self._material.setProtection(1)
        self._resource.setProtection(1)

        self.assertEqual(self._conf.getAccessController().isFullyPrivate(), True)
        self.assertEqual(self._contrib1.getAccessController().isFullyPrivate(), True)
        self.assertEqual(self._contrib2.getAccessController().isFullyPrivate(), True)
        self.assertEqual(self._session1.getAccessController().isFullyPrivate(), True)
        self.assertEqual(self._session2.getAccessController().isFullyPrivate(), True)
        self.assertEqual(self._material.getAccessController().isFullyPrivate(), True)
        self.assertEqual(self._resource.getAccessController().isFullyPrivate(), True)

    @with_context('database')
    def testPrivateInPublic(self):
        self._contrib2.setProtection(1)
        self._session2.setProtection(1)
        self._resource.setProtection(1)

        self.assertEqual(self._session1.getAccessController().isFullyPublic(), False)
        self.assertEqual(self._conf.getAccessController().isFullyPublic(), False)
        self.assertEqual(self._session1.getAccessController().getProtectedChildren(), [self._contrib2])
        self.assertEqual(self._contrib1.getAccessController().getProtectedChildren(), [self._resource])
        self.assertEqual(self._material.getAccessController().getProtectedChildren(), [self._resource])
        self.assertEqual(set(self._conf.getAccessController().getProtectedChildren()), set([self._contrib2, self._session2, self._resource]))

        self._contrib1.removeMaterial(self._material)

        self.assertEqual(self._contrib1.getAccessController().isFullyPublic(), True)
        self.assertEqual(self._material.getAccessController().getProtectedChildren(), [])
        self.assertEqual(set(self._conf.getAccessController().getProtectedChildren()), set([self._contrib2, self._session2]))

        self._conf.removeContribution(self._contrib2)

        self.assertEqual(self._session1.getAccessController().isFullyPublic(), True)
        self.assertEqual(self._session1.getAccessController().getProtectedChildren(), [])
        self.assertEqual(self._conf.getAccessController().getProtectedChildren(), [self._session2])

    @with_context('database')
    def testPublicInPrivate(self):
        self._conf.setProtection(1)
        self._contrib2.setProtection(-1)
        self._session2.setProtection(-1)
        self._resource.setProtection(-1)

        self.assertEqual(self._session1.getAccessController().isFullyPrivate(), False)
        self.assertEqual(self._conf.getAccessController().isFullyPrivate(), False)
        self.assertEqual(self._session1.getAccessController().getPublicChildren(), [self._contrib2])
        self.assertEqual(self._contrib1.getAccessController().getPublicChildren(), [self._resource])
        self.assertEqual(self._material.getAccessController().getPublicChildren(), [self._resource])
        self.assertEqual(set(self._conf.getAccessController().getPublicChildren()), set([self._contrib2, self._session2, self._resource]))

        self._contrib1.removeMaterial(self._material)

        self.assertEqual(self._contrib1.getAccessController().isFullyPrivate(), True)
        self.assertEqual(self._material.getAccessController().getPublicChildren(), [])
        self.assertEqual(set(self._conf.getAccessController().getPublicChildren()), set([self._contrib2, self._session2]))

        self._conf.removeContribution(self._contrib2)

        self.assertEqual(self._session1.getAccessController().isFullyPrivate(), True)
        self.assertEqual(self._session1.getAccessController().getPublicChildren(), [])
        self.assertEqual(self._conf.getAccessController().getPublicChildren(), [self._session2])
