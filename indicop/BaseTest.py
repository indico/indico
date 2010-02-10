# -*- coding: utf-8 -*-
##
## $Id$
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


import os
import tempfile
import transaction
import signal
import shutil
import commands
import sys
from TestsConfig import TestsConfig
from MaKaC.common.db import DBMgr

class BaseTest(object):
    #path to this current file
    setupDir = os.path.dirname(__file__)

    def startMessage(self, message):
        print "##################################################################"
        print "#####     %s" % message
        print "##################################################################\n"

    def writeReport(self, filename, content):
        try:
            f = open(os.path.join(self.setupDir, 'report', filename + ".txt"), 'w')
            f.write(content)
            f.close()
            return ""
        except IOError:
            return "Unable to write in %s, check your file permissions." % \
                    os.path.join(self.setupDir, 'report', filename + ".txt")

#    def createDummyUser(self):
#        from MaKaC import user
#        from MaKaC.authentication import AuthenticatorMgr
#        from MaKaC.common import HelperMaKaCInfo
#        from MaKaC.common import indexes
#        DBMgr.getInstance().startRequest()
#
#        #filling info to new user
#        avatar = user.Avatar()
#        avatar.setName( "fake" )
#        avatar.setSurName( "fake" )
#        avatar.setOrganisation( "fake" )
#        avatar.setLang( "en_US" )
#        avatar.setEmail( "fake@fake.fake" )
#
#        #registering user
#        ah = user.AvatarHolder()
#        ah.add(avatar)
#
#        #setting up the login info
#        li = user.LoginInfo( "dummyuser", "dummyuser" )
#        ih = AuthenticatorMgr()
#        userid = ih.createIdentity( li, avatar, "Local" )
#        ih.add( userid )
#
#        #activate the account
#        avatar.activateAccount()
#
#        #since the DB is empty, we have to add dummy user as admin
#        minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
#        al = minfo.getAdminList()
#        al.grant( avatar )
#
#        DBMgr.getInstance().endRequest()
#
#    def deleteDummyUser(self):
#        from MaKaC import user
#        from MaKaC.authentication import AuthenticatorMgr
#        from MaKaC.common import HelperMaKaCInfo
#        from MaKaC.common import indexes
#        DBMgr.getInstance().startRequest()
#
#        #removing user from admin list
#        minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
#        al = minfo.getAdminList()
#        ah = user.AvatarHolder()
#        avatar = ah.match({'email':'fake@fake.fake'})[0]
#        al.revoke( avatar )
#
#        #remove the login info
#        userid = avatar.getIdentityList()[0]
#        ih = AuthenticatorMgr()
#        ih.removeIdentity(userid)
#
#        #unregistering the user info
#        index = indexes.IndexesHolder().getById("email")
#        index.unindexUser(avatar)
#        index = indexes.IndexesHolder().getById("name")
#        index.unindexUser(avatar)
#        index = indexes.IndexesHolder().getById("surName")
#        index.unindexUser(avatar)
#        index = indexes.IndexesHolder().getById("organisation")
#        index.unindexUser(avatar)
#        index = indexes.IndexesHolder().getById("status")
#        index.unindexUser(avatar)

        #removing user from list
        la = ih.getById("Local")
        la.remove(userid)
        ah.remove(avatar)

        DBMgr.getInstance().endRequest()

    def walkThroughFolders(self, rootPath, foldersPattern):
        """scan a directory and return folders which match the pattern"""

        rootPluginsPath = os.path.join(rootPath)
        foldersArray = []

        for root, dirs, files in os.walk(rootPluginsPath):
            if root.endswith(foldersPattern) > 0:
                foldersArray.append(root)

        return foldersArray
