# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.


from MaKaC.common import HelperMaKaCInfo
from MaKaC.conference import CategoryManager, DefaultConference
from MaKaC.user import Avatar, AvatarHolder, LoginInfo
from MaKaC.authentication import AuthenticatorMgr


def initialize_new_db(root):
    """
    Initializes a new DB in debug mode
    """

    # Reset everything
    for e in root.keys():
        del root[e]

    # initialize db root
    cm = CategoryManager()
    cm.getRoot()

    home = cm.getById('0')

    # set debug mode on
    minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
    minfo.setDebugActive(True)

    return home


def create_user(name, login, authManager):
        avatar = Avatar()
        avatar.setName(name)
        avatar.setSurName(name)
        avatar.setOrganisation("fake")
        avatar.setLang("en_GB")
        avatar.setEmail("%s@fake.fake" % name)

        # setting up the login info
        li = LoginInfo(login, login)
        userid = authManager.createIdentity(li, avatar, "Local")
        authManager.add(userid)
        # activate the account
        avatar.activateAccount()
        return avatar


def create_dummy_users():
    """
    Creates a dummy user for testing purposes
    """
    minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
    ah = AvatarHolder()
    authManager = AuthenticatorMgr()
    avatars = []
    al = minfo.getAdminList()

    avatar = create_user("fake", "dummyuser", authManager)
    ah.add(avatar)
    avatars.append(avatar)
    al.grant(avatar)

    for i in xrange(1, 5):
        avatar = create_user("fake-%d" % i, "fake-%d" % i, authManager)
        avatar.setId("fake-%d" % i)
        ah.add(avatar)
        avatars.append(avatar)

    # since the DB is empty, we have to add dummy user as admin
    minfo = HelperMaKaCInfo.getMaKaCInfoInstance()

    dc = DefaultConference()
    HelperMaKaCInfo.getMaKaCInfoInstance().setDefaultConference(dc)
    return avatars
