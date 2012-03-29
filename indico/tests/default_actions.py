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
