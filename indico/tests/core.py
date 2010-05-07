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

from indico.tests.util import colored
from indico.tests.config import TestConfig
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

    def main(self, fakeDBPolicy, testsToRun, options):
        """
        Runs the main test cycle, iterating over all the TestRunners available

         * fakeDBPolicy - see startManageDB()
         * testsToRun - a list of strings specifying which tests to run
         * options - test options (such as verbosity...)
        """

        returnString = "\n\n%s\n\n" % colored('** Results', 'blue', attrs = ['bold'])

        #To not pollute the installation of Indico
        self._configureTempFolders()


        self._startManageDB(fakeDBPolicy)

        if options['coverage']:
            CoverageTestRunner.instantiate()

        #specified test can either be unit or functional.
        if options['specify']:
            returnString += SpecificFunctionalTestRunner(options['specify']).run()
        else:
            for test in testsToRun:
                if test in TEST_RUNNERS:
                    returnString += TEST_RUNNERS[test](**options).run()
                else:
                    returnString += colored("[ERR] Test set '%s' does not exist. "
                      "It has to be added in the TEST_RUNNERS variable\n", 'red') \
                    % test


        self._stopManageDB(fakeDBPolicy)

        self._deleteTempFolders()

        return returnString

    def _configureTempFolders(self):
        """
        Creates temporary directories for the archive and uploaded files
        """

        keyNames = [#'LogDir',
                    'ArchiveDir',
                    'UploadedFilesTempDir']

        for key in keyNames:
            self.tempDirs[key] = tempfile.mkdtemp()

        Config.getInstance().updateValues(self.tempDirs)

    def _deleteTempFolders(self):
        """
        Deletes the temporary folders
        """
        for k in self.tempDirs:
            shutil.rmtree(self.tempDirs[k])

################## Start of DB Managing functions ##################
    def _startManageDB(self, fakeDBPolicy):
        """
        Stops the production DB (if needed) and starts a temporary / fake DB

        * fakeDBPolicy == 0, the tests to run do not need any DB
        * fakeDBPolicy == 1, unit tests need a fake DB that can be run in parallel
        with the production DB
        * fakeDBPolicy == 2, production DB is not running and functional tests
        need fake DB which is going to be run on production port.
        fakeDBPolicy == 3, production DB is running, we need to stop it and
        and start a fake DB on the production port. we will restart production DB
        """

        if fakeDBPolicy == 1:
            self._startFakeDB(TestConfig.getInstance().getFakeDBPort())
            TestManager._createDummyUser()
        elif fakeDBPolicy == 2:
            self._startFakeDB(Config.getInstance().getDBConnectionParams()[1])
            TestManager._createDummyUser()
        elif fakeDBPolicy == 3:
            TestManager._stopProductionDB()
            self._startFakeDB(Config.getInstance().getDBConnectionParams()[1])
            TestManager._createDummyUser()

    def _stopManageDB(self, fakeDBPolicy):
        """
        Stops the temporary DB and restarts the production DB if needed
        """
        if fakeDBPolicy == 1 or fakeDBPolicy == 2:
            self._stopFakeDB()
            TestManager._restoreDBInstance()
        elif fakeDBPolicy == 3:
            self._stopFakeDB()
            TestManager._startProductionDB()
            TestManager._restoreDBInstance()

    def _startFakeDB(self, zeoPort):
        """
        Starts a temporary DB in a different port
        """
        self._createNewDBFile()
        self.zeoServer = TestManager._createDBServer(
            os.path.join(self.dbFolder, "Data.fs"),
            zeoPort)

        DBMgr.setInstance(DBMgr(hostname="localhost", port=zeoPort))

    def _stopFakeDB(self):
        """
        Stops the temporary DB
        """
        try:
            os.kill(self.zeoServer, signal.SIGINT)
        except OSError, e:
            print ("Problem sending kill signal: " + str(e))

        try:
            os.waitpid(self.zeoServer, 0)
            self._removeDBFile()
        except OSError, e:
            print ("Problem waiting for ZEO Server: " + str(e))

    @staticmethod
    def _restoreDBInstance():
        """
        Resets the DB instance in the DBMgr
        """
        DBMgr.setInstance(None)

    @staticmethod
    def _startProductionDB():
        """
        Starts the 'production' db (the one configured in indico.conf)
        """
        try:
            commands.getstatusoutput(TestConfig.getInstance().getStartDBCmd())
        except KeyError:
            print "[ERR] Not found in tests.conf: command to start production DB\n"
            sys.exit(1)

    @staticmethod
    def _stopProductionDB():
        """
        Stops the 'production' DB
        """
        try:
            commands.getstatusoutput(TestConfig.getInstance().getStopDBCmd())
        except KeyError:
            print "[ERR] Not found in tests.conf: command to stop production DB\n"
            sys.exit(1)

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

    @staticmethod
    def _createDBServer(dbFile, port):
        """
        Creates a fake DB server for testing
        """

        pid = os.fork()
        if pid:
            return pid
        else:
            # run a DB in a child process
            from indico.tests.util import TestZEOServer
            server = TestZEOServer(port, dbFile)
            server.start()

################## End of DB Managing functions ##################

    @staticmethod
    def _createDummyUser():
        """
        Creates a test user in the DB
        """
        from MaKaC import user
        from MaKaC.authentication import AuthenticatorMgr
        from MaKaC.common import HelperMaKaCInfo

        DBMgr.getInstance().startRequest()

        #filling info to new user
        avatar = user.Avatar()
        avatar.setName( "fake" )
        avatar.setSurName( "fake" )
        avatar.setOrganisation( "fake" )
        avatar.setLang( "en_US" )
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
