# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN)
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


def create_dummy_user():
    """
    Creates a dummy user for testing purposes
    """
    avatar = Avatar()

    avatar.setName("fake")
    avatar.setSurName("fake")
    avatar.setOrganisation("fake")
    avatar.setLang("en_GB")
    avatar.setEmail("fake@fake.fake")

    # registering user
    ah = AvatarHolder()
    ah.add(avatar)

    # setting up the login info
    li = LoginInfo("dummyuser", "dummyuser")
    ih = AuthenticatorMgr()
    userid = ih.createIdentity(li, avatar, "Local")
    ih.add(userid)

    # activate the account
    avatar.activateAccount()

    # since the DB is empty, we have to add dummy user as admin
    minfo = HelperMaKaCInfo.getMaKaCInfoInstance()

    al = minfo.getAdminList()
    al.grant(avatar)

    dc = DefaultConference()
    HelperMaKaCInfo.getMaKaCInfoInstance().setDefaultConference(dc)
    return avatar
