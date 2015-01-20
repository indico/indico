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

# For now, disable Pylint
# pylint: disable-all

from datetime import datetime
from pytz import timezone
from indico.tests.env import *

from MaKaC.user import Avatar
from MaKaC.conference import AvatarHolder, AdminList, Conference, Contribution,\
    ConferenceHolder
from MaKaC import conference
from indico.tests.python.unit.util import IndicoTestCase, with_context
from MaKaC.review import AbstractStatusWithdrawn, AbstractStatusSubmitted


class TestAbstractSubmission(IndicoTestCase):

    _requires = ['db.Database', 'db.DummyUser']

    def setUp(self):
        super(TestAbstractSubmission, self).setUp()

        with self._context("database"):
            # Create a conference
            category = conference.CategoryManager().getById('0')
            self._conf = category.newConference(self._avatar1)
            self._conf.setTimezone('UTC')
            sd = datetime(2011, 11, 1, 10, 0, tzinfo=timezone('UTC'))
            ed = datetime(2011, 11, 1, 18, 0, tzinfo=timezone('UTC'))
            self._conf.setDates(sd, ed)
            ch = ConferenceHolder()
            ch.add(self._conf)

    @with_context('database')
    def testSubmitAbstract(self):
        cfaMgr = self._conf.getAbstractMgr()

        self.assertEqual(len(cfaMgr.getAbstractList()), 0)
        # Create an abstract
        a = cfaMgr.newAbstract(self._avatar1)
        a_set = frozenset((a,))
        # It should be the only one in the list
        self.assertEqual(frozenset(cfaMgr.getAbstractList()), a_set)
        # Create another one
        cfaMgr.newAbstract(self._avatar3)
        # The first abstract should be searchable through the avatar and email
        self.assertEqual(frozenset(cfaMgr.getAbstractListForAvatar(self._avatar1)), a_set)
        self.assertEqual(frozenset(cfaMgr.getAbstractListForAuthorEmail(self._avatar1.getEmail())), a_set)
        # Other avatar shouldn't have any abstracts
        self.assertFalse(cfaMgr.getAbstractListForAvatar(self._avatar2))
        self.assertFalse(cfaMgr.getAbstractListForAuthorEmail(self._avatar2.getEmail()))
        # Test searching by email
        a.newPrimaryAuthor(title='Prof', firstName='Pinky', surName='Brain', email='brain@bugs.xyz',
                                  affiliation='Secret Laboratory', address='', telephone='')
        self.assertEqual(frozenset(cfaMgr.getAbstractListForAuthorEmail('brain@bugs.xyz')), a_set)
        self.assertFalse(cfaMgr.getAbstractListForAuthorEmail('more@bugs.xyz'))
        a.newCoAuthor(title='Dr', firstName='Elektra', surName='King', email='world@domination.xyz',
                                  affiliation='Secret Laboratory', address='', telephone='')
        self.assertEqual(frozenset(cfaMgr.getAbstractListForAuthorEmail('world@domination.xyz')), a_set)
        # Withdraw the abstract - it should be still available!
        self.assertTrue(isinstance(a.getCurrentStatus(), AbstractStatusSubmitted))
        a.withdraw(self._avatar1, 'Test')
        self.assertTrue(isinstance(a.getCurrentStatus(), AbstractStatusWithdrawn))
        self.assertEqual(frozenset(cfaMgr.getAbstractListForAvatar(self._avatar1)), a_set)
        self.assertEqual(frozenset(cfaMgr.getAbstractListForAuthorEmail(self._avatar1.getEmail())), a_set)
        self.assertEqual(frozenset(cfaMgr.getAbstractListForAuthorEmail('brain@bugs.xyz')), a_set)
        self.assertEqual(frozenset(cfaMgr.getAbstractListForAuthorEmail('world@domination.xyz')), a_set)
