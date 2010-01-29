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
from MaKaC import user
from MaKaC.authentication import AuthenticatorMgr
from MaKaC.common import HelperMaKaCInfo
from MaKaC.common import indexes

class BaseTest(object):
    #path to this current file
    setupDir = os.path.dirname(__file__)

    def __init__(self):
        self.al = None
        self.ah = None
        self.avatar = None
        self.ih = None

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

    def createDummyUser(self):
        from Indicop import Indicop
        Indicop.getInstance(None, None).getDBInstance().startRequest()

        #filling info to new user
        self.avatar = user.Avatar()
        self.avatar.setName( "fake" )
        self.avatar.setSurName( "fake" )
        self.avatar.setOrganisation( "fake" )
        self.avatar.setLang( "en_US" )
        self.avatar.setEmail( "fake@fake.fake" )

        #registering user
        self.ah = user.AvatarHolder()
        self.ah.add(self.avatar)

        #setting up the login info
        li = user.LoginInfo( "dummyuser", "dummyuser" )
        self.ih = AuthenticatorMgr()
        userid = self.ih.createIdentity( li, self.avatar, "Local" )
        self.ih.add( userid )

        #activate the account
        self.avatar.activateAccount()

        #since the DB is empty, we have to add dummy user as admin
        minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
        self.al = minfo.getAdminList()
        self.al.grant( self.avatar )

        Indicop.getInstance(None, None).getDBInstance().endRequest()

    def deleteDummyUser(self):
        from Indicop import Indicop
        Indicop.getInstance(None, None).getDBInstance().startRequest()

        #removing user from admin list
        self.al.revoke( self.avatar )

        #remove the login info
        userid = self.avatar.getIdentityList()[0]
        self.ih.removeIdentity(userid)

        #unregistering the user info
        index = indexes.IndexesHolder().getById("email")
        index.unindexUser(self.avatar)
        index = indexes.IndexesHolder().getById("name")
        index.unindexUser(self.avatar)
        index = indexes.IndexesHolder().getById("surName")
        index.unindexUser(self.avatar)
        index = indexes.IndexesHolder().getById("organisation")
        index.unindexUser(self.avatar)
        index = indexes.IndexesHolder().getById("status")
        index.unindexUser(self.avatar)

        #removing user from list
        la = self.ih.getById("Local")
        la.remove(userid)
        self.ah.remove(self.avatar)

        Indicop.getInstance(None, None).getDBInstance().endRequest()

    def walkThroughFolders(self, rootPath, foldersPattern):
        """scan a directory and return folders which match the pattern"""

        rootPluginsPath = os.path.join(rootPath)
        foldersArray = []

        for root, dirs, files in os.walk(rootPluginsPath):
            if root.endswith(foldersPattern) > 0:
                foldersArray.append(root)

        return foldersArray


################################################
#    To be deleted when we get rid of mod_python
################################################
    def createDummyUserDeprecated(self):
        from MaKaC.common.db import DBMgr
        self.fakedb = DBMgr().getInstance()
        self.fakedb._db.close()
        self.db = DBMgr()
        DBMgr.setInstance(self.db)
        self.db.startRequest()

        #filling info to new user
        self.avatarD = user.Avatar()
        self.avatarD.setName( "fake" )
        self.avatarD.setSurName( "fake" )
        self.avatarD.setOrganisation( "fake" )
        self.avatarD.setLang( "en_US" )
        self.avatarD.setEmail( "fake@fake.fake" )

        #registering user
        self.ahD = user.AvatarHolder()
        self.ahD.add(self.avatarD)

        #setting up the login info
        liD = user.LoginInfo( "dummyuser", "dummyuser" )
        self.ihD = AuthenticatorMgr()
        useridD = self.ihD.createIdentity( liD, self.avatarD, "Local" )
        self.ihD.add( useridD )

        #activate the account
        self.avatarD.activateAccount()

        #since the DB is empty, we have to add dummy user as admin
        minfoD = HelperMaKaCInfo.getMaKaCInfoInstance()
        self.alD = minfoD.getAdminList()
        self.alD.grant( self.avatarD )

        self.db.endRequest(True)

    def deleteDummyUserDeprecated(self):
        from MaKaC.common.db import DBMgr
        self.db.startRequest()

        #removing user from admin list
        self.alD.revoke( self.avatarD )

        #remove the login info
        useridD = self.avatarD.getIdentityList()[0]
        self.ihD.removeIdentity(useridD)

        #unregistering the user info
        index = indexes.IndexesHolder().getById("email")
        index.unindexUser(self.avatarD)
        index = indexes.IndexesHolder().getById("name")
        index.unindexUser(self.avatarD)
        index = indexes.IndexesHolder().getById("surName")
        index.unindexUser(self.avatarD)
        index = indexes.IndexesHolder().getById("organisation")
        index.unindexUser(self.avatarD)
        index = indexes.IndexesHolder().getById("status")
        index.unindexUser(self.avatarD)

        #removing user from list
        laD = self.ihD.getById("Local")
        laD.remove(useridD)
        self.ahD.remove(self.avatarD)

        self.db.endRequest(True)

################################################
#            end of block
################################################