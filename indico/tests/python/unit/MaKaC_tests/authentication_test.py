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

from MaKaC.user import Avatar, AvatarHolder, Group, GroupHolder, LoginInfo
from MaKaC.authentication import AuthenticatorMgr
from indico.tests.python.unit.util import IndicoTestCase, with_context

class TestAuthentication(IndicoTestCase):

    _requires = ['db.Database']

    def setUp(self):
        super(TestAuthentication, self).setUp()

        with self._context("database"):

            # Create few users and groups
            gh = GroupHolder()
            ah = AvatarHolder()
            self._authMgr = AuthenticatorMgr()

            for i in xrange(1, 5):
                group = Group()
                group.setName("fake-group-%d" % i)
                group.setDescription("fake")
                group.setEmail("fake-group-%d@fake.fake" % i)
                group.setId("fake-group-%d" % i)
                avatar = Avatar()
                avatar.setName("fake-%d" % i)
                avatar.setSurName("fake")
                avatar.setOrganisation("fake")
                avatar.setLang("en_GB")
                avatar.setEmail("fake%d@fake.fake" % i)
                avatar.setId("fake-%d" % i)
                avatar.activateAccount()
                group.addMember(avatar)
                ah.add(avatar)
                gh.add(group)
                identity = self._authMgr.createIdentity(LoginInfo("fake-%d" % i, "fake-%d" % i), avatar, "Local")
                self._authMgr.add(identity)

    @with_context('database')
    def testAvatarHolder(self):
        """
        Test Avatar Holder
        """
        ah = AvatarHolder()
        self.assertEqual(ah.getById("fake-1").getName(), "fake-1")
        self.assertEqual(ah.match({"name": "fake-1"}, searchInAuthenticators=False)[0].getEmail(), "fake1@fake.fake")
        self.assertEqual(len(ah.matchFirstLetter("name", "f" ,searchInAuthenticators=False)), 4)

    @with_context('database')
    def testGroupHolder(self):
        gh = GroupHolder()
        ah = AvatarHolder()
        self.assert_(gh.getById("fake-group-1").containsUser(ah.getById("fake-1")))
        self.assertEqual(gh.match({"groupname": "fake-group-1"}, searchInAuthenticators=False)[0].getEmail(), "fake-group-1@fake.fake")
        self.assertEqual(len(gh.matchFirstLetter("f" ,searchInAuthenticators=False)), 4)

    @with_context('database')
    def testIdentities(self):
        ah = AvatarHolder()
        for i in xrange(1, 5):
            self.assertEqual(self._authMgr.getAvatar(LoginInfo("fake-%d"%i, "fake-%d"%i)), ah.getById("fake-%d"%i))
