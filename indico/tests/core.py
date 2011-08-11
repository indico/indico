# -*- coding: utf-8 -*-
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

# pylint: disable-msg=W0401

"""
This is the very core of indico.tests
Here is defined the TestManager class, that provides a single point of access
to the outside world.
"""

# System modules
import os, sys, shutil, signal, commands, tempfile

# Database
import transaction
from MaKaC.common.db import DBMgr

# Indico
from MaKaC.common.Configuration import Config

from indico.util.console import colored
from indico.tests.config import TestConfig
from indico.tests.base import TestOptionException, FakeMailThread

from indico.tests.runners import *

TEST_RUNNERS = {'unit': UnitTestRunner,
                'functional': FunctionalTestRunner,
                'pylint': PylintTestRunner,
                'jsunit': JSUnitTestRunner,
                'jslint': JSLintTestRunner,
                'grid': GridTestRunner}


class TestManager(object):
    """
    Main class, the heart of the test API.
    Launches all the tests according to the parameters that are passed
    """

    __instance = None

    def __init__(self):
        """
        Initializes the object
        """
        self.dbmgr = None
        self.zeoServer = None
        self.tempDirs = {}
        self.dbFolder = None

    @staticmethod
    def _title(text):
        """
        Prints an title
        """
        print colored("-- " + str(text), 'yellow', attrs=['bold'])

    @staticmethod
    def _info(message):
        """
        Prints an info message
        """
        print colored("-- " + str(message), 'cyan')

    @staticmethod
    def _error(message):
        """
        Prints an info message
        """
        print colored("-- " + str(message), 'red')

    @staticmethod
    def _debug(message):
        """
        Prints an info message
        """
        print colored("-- " + str(message), 'grey')

    def main(self, testsToRun, options):
        """
        Runs the main test cycle, iterating over all the TestRunners available

         * testsToRun - a list of strings specifying which tests to run
         * options - test options (such as verbosity...)
        """
        result = False

        print
        TestManager._title("Starting test framework\n")

        self._setFakeConfig()

        self._startSMTPServer()
        self._startManageDB()

        try:
            for test in testsToRun:
                if test in TEST_RUNNERS:
                    try:
                        result = TEST_RUNNERS[test](**options).run()
                    except TestOptionException, e:
                        TestManager._error(e)
                else:
                    print colored("[ERR] Test set '%s' does not exist. "
                                  "It has to be added in the TEST_RUNNERS variable\n",
                                  'red') % test
        finally:
            # whatever happens, clean this mess up
            self._stopManageDB()
            self._stopSMTPServer()

        if result:
            return 0
        else:
            return -1

    def _setFakeConfig(self):
        config = Config.getInstance()
        config.updateValues(Config.default_values)
        config.updateValues({
            'SmtpServer': ('localhost', 8025),
            'SmtpUseTLS': 'no',
            'DBConnectionParams': ('localhost', 59675)
            })

        temp = tempfile.mkdtemp(prefix="indico_")
        self._info('Using %s as temporary dir' % temp)

        config.updateValues({
            'LogDir': os.path.join(temp, 'log'),
            'XMLCacheDir': os.path.join(temp, 'cache'),
            'ArchiveDir': os.path.join(temp, 'archive'),
            'UploadedFilesTempDir': os.path.join(temp, 'tmp'),
            'TempDir': os.path.join(temp, 'tmp')
            })

        Config.setInstance(config)
        self._cfg = config

################## Start of DB Managing functions ##################
    def _startManageDB(self):

        params = Config.getInstance().getDBConnectionParams()
        port = TestConfig.getInstance().getFakeDBPort()

        self._info("Starting fake DB in port %s" % port)
        self._startFakeDB('localhost', port)
        TestManager._createDummyUser()
        TestManager._setDebugMode()

    def _stopManageDB(self):
        """
        Stops the temporary DB
        """
        self._stopFakeDB()

    def _startFakeDB(self, zeoHost, zeoPort):
        """
        Starts a temporary DB in a different port
        """

        print colored("-- Starting a test DB", "cyan")

        self._createNewDBFile()
        self.zeoServer = TestManager._createDBServer(
            os.path.join(self.dbFolder, "Data.fs"),
            zeoHost, zeoPort)

        DBMgr.setInstance(DBMgr(hostname=zeoHost, port=zeoPort))

    def _stopFakeDB(self):
        """
        Stops the temporary DB
        """

        print colored("-- Stopping test DB", "cyan")

        try:
            self.zeoServer.shutdown()
            self._removeDBFile()
        except OSError, e:
            print ("Problem terminating ZEO Server: " + str(e))

    def _createNewDBFile(self):
        """
        Creates a new DB file for a temporary DB
        """
        from ZODB import FileStorage, DB
        savedDir = os.getcwd()
        self.dbFolder = tempfile.mkdtemp()
        os.chdir(self.dbFolder)

        storage = FileStorage.FileStorage("Data.fs")
        db = DB(storage)
        connection = db.open()

        transaction.commit()

        connection.close()
        db.close()
        storage.close()
        os.chdir(savedDir)

    def _removeDBFile(self):
        """
        Removes the files of the temporary DB
        """
        shutil.rmtree(self.dbFolder)

    @classmethod
    def _startSMTPServer(cls):
        cls._smtpd = FakeMailThread(('localhost', 8025))
        cls._smtpd.start()

    @classmethod
    def _stopSMTPServer(cls):
        cls._smtpd.close()

    @staticmethod
    def _createDBServer(dbFile, host, port):
        """
        Creates a fake DB server for testing
        """

        # run a DB in a child process
        from indico.tests.util import TestZEOServer
        server = TestZEOServer(port, dbFile, hostname = host)
        server.start()
        return server

################## End of DB Managing functions ##################

    @staticmethod
    def _createDummyUser():
        """
        Creates a test user in the DB
        """
        from MaKaC import user
        from MaKaC.authentication import AuthenticatorMgr
        from MaKaC.common import HelperMaKaCInfo

        TestManager._info("Adding a dummy user")

        DBMgr.getInstance().startRequest()

        #filling info to new user
        avatar = user.Avatar()
        avatar.setName( "fake" )
        avatar.setSurName( "fake" )
        avatar.setOrganisation( "fake" )
        avatar.setLang( "en_GB" )
        avatar.setEmail( "fake@fake.fake" )

        #registering user
        ah = user.AvatarHolder()
        ah.add(avatar)

        #setting up the login info
        li = user.LoginInfo( "dummyuser", "dummyuser" )
        ih = AuthenticatorMgr()
        userid = ih.createIdentity( li, avatar, "Local" )
        ih.add( userid )

        #activate the account
        avatar.activateAccount()

        #since the DB is empty, we have to add dummy user as admin
        minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
        al = minfo.getAdminList()
        al.grant( avatar )

        DBMgr.getInstance().endRequest()

    @staticmethod
    def _deleteDummyUser():
        """
        Deletes the test user from the DB
        """

        from MaKaC import user
        from MaKaC.authentication import AuthenticatorMgr
        from MaKaC.common import HelperMaKaCInfo
        from MaKaC.common import indexes

        TestManager._info("Deleting dummy user", "cyan")

        DBMgr.getInstance().startRequest()

        #removing user from admin list
        minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
        al = minfo.getAdminList()
        ah = user.AvatarHolder()
        avatar = ah.match({'email':'fake@fake.fake'})[0]
        al.revoke( avatar )

        #remove the login info
        userid = avatar.getIdentityList()[0]
        ih = AuthenticatorMgr()
        ih.removeIdentity(userid)

        #unregistering the user info
        index = indexes.IndexesHolder().getById("email")
        index.unindexUser(avatar)
        index = indexes.IndexesHolder().getById("name")
        index.unindexUser(avatar)
        index = indexes.IndexesHolder().getById("surName")
        index.unindexUser(avatar)
        index = indexes.IndexesHolder().getById("organisation")
        index.unindexUser(avatar)
        index = indexes.IndexesHolder().getById("status")
        index.unindexUser(avatar)

        DBMgr.getInstance().endRequest()


    @staticmethod
    def _setDebugMode():
        """
        Sets the Debug Mode for the DB
        """
        from MaKaC.common import HelperMaKaCInfo

        TestManager._info("Starting up debug mode")

        DBMgr.getInstance().startRequest()

        #debug mode
        minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
        minfo.setDebugActive()

        DBMgr.getInstance().endRequest()
