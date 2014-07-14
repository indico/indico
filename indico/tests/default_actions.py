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

import os

from MaKaC.common import HelperMaKaCInfo
from MaKaC.conference import CategoryManager, DefaultConference
from MaKaC.user import Avatar, AvatarHolder, LoginInfo, Group, GroupHolder
from MaKaC.authentication import AuthenticatorMgr
from indico.core.config import Config
from indico.util.fs import delete_recursively


def initialize_new_db(root):
    """
    Initializes a new DB in debug mode
    """

    # Reset everything
    for e in root.keys():
        del root[e]

    # Delete whoosh indexes
    whoosh_dir = os.path.join(Config.getInstance().getArchiveDir(), 'whoosh')
    if os.path.exists(whoosh_dir):
        delete_recursively(whoosh_dir)

    # initialize db root
    cm = CategoryManager()
    cm.getRoot()

    return cm.getById('0')


def create_user(name, login, authManager, set_password=False):
    avatar = Avatar()
    avatar.setName(name)
    avatar.setSurName(name)
    avatar.setOrganisation("fake")
    avatar.setLang("en_GB")
    avatar.setEmail("%s@fake.fake" % name)

    # setting up the login info
    li = LoginInfo(login, login if set_password else None)
    userid = authManager.createIdentity(li, avatar, "Local")
    authManager.add(userid)
    # activate the account
    avatar.activateAccount()
    return avatar


def create_group(name, description, email):
    group = Group()
    group.setName(name)
    group.setDescription(description)
    group.setEmail(email)
    return group


def create_dummy_users(dummyuser_has_password=False):
    """
    Creates a dummy user for testing purposes.

    If dummyuser_has_password is set, "dummyuser" and "fake-1" can be used for logging in.
    """
    minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
    ah = AvatarHolder()
    authManager = AuthenticatorMgr()
    avatars = []
    al = minfo.getAdminList()

    avatar = create_user("fake", "dummyuser", authManager, dummyuser_has_password)
    ah.add(avatar)
    avatars.append(avatar)
    al.grant(avatar)

    for i in xrange(1, 5):
        avatar = create_user("fake-%d" % i, "fake-%d" % i, authManager, dummyuser_has_password and i == 1)
        avatar.setId("fake-%d" % i)
        ah.add(avatar)
        avatars.append(avatar)

    HelperMaKaCInfo.getMaKaCInfoInstance().setDefaultConference(DefaultConference())
    return avatars


def create_dummy_group():
    """
    Creates a dummy group for testing purposes.
    """
    gh = GroupHolder()
    dummy_group = create_group("fake_group", "fake", "fake@fk.com")
    gh.add(dummy_group)
    return dummy_group
