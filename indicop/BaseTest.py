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
import sys
import nose
import figleaf
import figleaf.annotate_html
import subprocess
import socket
import time
import commands
import StringIO
import signal
import BaseTest
from selenium import selenium
from MaKaC.common.db import DBMgr
from MaKaC import user
from MaKaC.authentication import AuthenticatorMgr
from MaKaC.common import HelperMaKaCInfo
from MaKaC.common import indexes
from ZEO.runzeo import ZEOOptions, ZEOServer

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
        DBMgr.getInstance().startRequest()

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

        DBMgr.getInstance().endRequest()

    def deleteDummyUser(self):
        DBMgr.getInstance().startRequest()

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

        DBMgr.getInstance().endRequest()

    def walkThroughFolders(self, rootPath, foldersPattern):
        """scan a directory and return folders which match the pattern"""

        rootPluginsPath = os.path.join(rootPath)
        foldersArray = []

        for root, dirs, files in os.walk(rootPluginsPath):
            if root.endswith(foldersPattern) > 0:
                foldersArray.append(root)

        return foldersArray

