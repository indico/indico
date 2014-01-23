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

# For now, disable Pylint
# pylint: disable-all


from indico.core.db import DBMgr
from MaKaC.conference import ConferenceHolder
from random import Random
from MaKaC.plugins.Collaboration.services import CollaborationRemoveCSBooking, CollaborationBookingIndexQuery, CollaborationCreateTestCSBooking
from MaKaC.plugins.Collaboration.actions import DeleteAllBookingsAction
from indico.core.index import Catalog
from MaKaC.common.indexes import IndexesHolder
from MaKaC.errors import MaKaCError
from indico.core.config import Config

from util import TestZEOServer

import math
import profile
import time
import logging
import traceback

import unittest
import shutil
import subprocess
import sys
import os, signal


################################### HOW TO USE THIS TEST ##################################
#
# There are 2 groups of configuration parameters.
#
# The 1st group (system and DB paths / configuration) deals with where some files are.
# Currently they point towards the correct locations in the CERN indicodev machine.
#
# The 2nd group deals with the extension of the test.
# This test will insert bookings randmonly in a range of conferences (going from firstConfId to lastConfId),
# trying to insert a number close to "startingBookings"
# Then it will run 4 tests:
# -add n bookings (where n = the "bookingsPerTest" variable)
# -remove n bookings (where n = the "bookingsPerTest" variable)
# -do n queries (where n = indexQueriesPerTest) to the index
# -remove n conferences (where n = removeConfsPerTest) and unindex all their bookings
#
# For this test to work, after an indico install, you need to go to
# /opt/indico/install/cds-indico-xxxxxxx/ and do:
# sudo python setup.py develop (in order to compile the .po to .mo)
# sudo vim setup.py and change INDICO_INSTALL = True to INDICO_INSTALL = False
#
# Also, this test assumes that you did a snapshot of the database in /opt/indico/db
# by copying the data.fs, data.fs.index, and data.fs.tmp into
# dbForTesting.fs, dbForTesting.fs.index, and dbForTesting.fs.tmp
#
#########################################################################################

config = Config.getInstance()

#system and DB paths / configuration
testingDbfile = '/tmp/data.fs'
collaborationDbFile = os.path.join(config.getUploadedFilesTempDir(), 'CollaborationTests-Data.fs')
zeoPort = 9685

pythonExecutable = sys.executable

#test configuration
firstConfId = 40000
lastConfId = 65000
startingBookings = 20000
bookingsPerTest = 100
indexQueriesPerTest = 50
removeConfsPerTest = 10
randomOpsPerTest = 50

startDate = '01/01/2008 00:00'
endDate = '31/12/2010 23:59'
dateFormat = '%d/%m/%Y %H:%M'

doProfile = False

makeCopy = True
doCleanUp = True
doRemove = True

def setup_module():
    #this test is a performance test and takes too much time to execute
    import nose
    raise nose.SkipTest

class TestResponsiveness(unittest.TestCase):

    def createDBServer(self, file, port):
        pid = os.fork()
        if pid:
            return pid
        else:
            server = TestZEOServer(port, file)
            server.start()

    def setUp(self):
        self.random = Random()
        self._loggingSetup()


        self._log("Start of test. Current pid is: " + str(os.getpid()))
        self._log("Initiating setUp of test")
        self._log('')

        try:
            if makeCopy:
                self._log("Copying " + testingDbfile + " to " + collaborationDbFile + " ...")
                try:
                    os.remove(collaborationDbFile)
                    os.remove(collaborationDbFile + '.index')
                    os.remove(collaborationDbFile + '.tmp')
                except:
                    pass

                shutil.copy(testingDbfile, collaborationDbFile)
                try:
                    shutil.copy(testingDbfile + '.index', collaborationDbFile + '.index')
                except:
                    self._log("problem copying "  + testingDbfile + '.index')
                try:
                    shutil.copy(testingDbfile + '.tmp', collaborationDbFile + '.tmp')
                except:
                    self._log("problem copying "  + testingDbfile + '.tmp')

                self._log("copy finished.")
                self._log('')

            self._log("Starting the ZEO server...")
            self.zeoServer = self.createDBServer(collaborationDbFile, zeoPort)
            self._log("zodb server started on pid: " + str(self.zeoServer) + " .")
            self._log('')


            self._log("Creating a CustomDBMgr on port " + str(zeoPort))
            self.cdbmgr = DBMgr.getInstance(hostname="localhost", port=zeoPort)
            self._log("Starting a request ...")
            self.cdbmgr.startRequest()
            self._log("Request started successfully.")
            self._log('')

            if doCleanUp:
                self._log('Cleaning the DB of bookings and recreating the indexes')
                DeleteAllBookingsAction(FalseAction()).call()
                self._log('Cleanup succesfull')

            self._log("We start populating DB with bookings...")

            #ConferenceHolder()._getIdx() is an OOBTree
            size = lastConfId - firstConfId
            self._log("Populating among aproximately " + str(size) + " events, from " + str(firstConfId) + " to " + str(lastConfId) + ", with aproximately " + str(startingBookings) + " bookings")
            self._log("Initial size of 'all' index: " + str(IndexesHolder().getById("Collaboration").getAllBookingsIndex().getCount()))

            self.validConfIds = []
            self.confsWithBookings = []

            populated = 0
            added = 0
            chance = (float(startingBookings) / float(size)) / 2.0
            ch = ConferenceHolder()

            for confId in xrange(firstConfId, lastConfId + 1):
                confId = str(confId)
                if self.random.random() < chance:
                    try:
                        conf = ch.getById(confId)
                        self.validConfIds.append(confId)
                    except MaKaCError:
                        continue
                    i = 0

                    bookingsForThisConf = max(int(self.random.normalvariate(3, 3)),0)
                    added += bookingsForThisConf
                    while i < bookingsForThisConf:
                        Catalog.getIdx("cs_bookingmanager_conference").get(conf.getId()).createTestBooking(bookingParams = {'startDate': self._randomDate(startDate, endDate)})
                        i += 1

                    populated += 1
                    self.confsWithBookings.append(confId)
                    if populated % 100 == 0:
                        self._log(str(populated) + ' events populated. Index size: ' + str (IndexesHolder().getById("Collaboration").getAllBookingsIndex().getCount()))


            self._log("Populating finished. " + str(populated) + " events populated with " + str(added) + " bookings")
            self._log("Size of 'all' index is now: " + str(IndexesHolder().getById("Collaboration").getAllBookingsIndex().getCount()))
            self._log("Performing commit...")

            self.cdbmgr.endRequest(True) #True = commmit
            self._log("End of request")
            self._log('')

        except Exception, e:
            tb = str(traceback.format_tb(sys.exc_info()[2]))
            self.logger.error("There was an exception in setUp. Calling tearDown. Exception: " + str(e) + ", Traceback = " + tb)
            self.tearDown()
            self.fail("setUp failed. Cause: " + str(e) + ", Traceback = " + tb)


    def tearDown(self):
        self._log("Initiating tearDown of test")
        self._log('')

        try:
            self._log("Sending kill signal to ZEO Server at pid " + str(self.zeoServer) + " ...")
            os.kill(self.zeoServer, signal.SIGTERM)
            self._log("Signal sent")
        except Exception, e:
            self._log("Problem sending kill signal: " + str(e))

        try:
            self._log("Waiting for ZEO Server to finish ...")
            os.wait()
            self._log("Zodb server finished.")
        except Exception, e:
            self._log("Problem waiting for ZEO Server: " + str(e))

        if doRemove:
            try:
                self._log("Removing " + collaborationDbFile + " ...")
                self._log(collaborationDbFile + " removed.")
            except Exception, e:
                self._log("Problem removing the test DB file: " + str(e))

        self._log("End of test")


    def testResponsiveness(self):
        self._log("Start of tests")
        self._log('')

        self._log("Starting add booking test")
        self._addBookingTest()
        self._log("End of add booking test. Normal time: avg= %.5fs, dev= %.5fs. CPU time: avg= %.5fs, dev= %.5fs." % (self.average, self.deviation, self.caverage, self.cdeviation))

        self._log("Starting remove booking test")
        self._removeBookingTest()
        self._log("End of remove booking test. Normal time: avg= %.5fs, dev= %.5fs. CPU time: avg= %.5fs, dev= %.5fs." % (self.average, self.deviation, self.caverage, self.cdeviation))

        self._log("Starting index query test")
        self._indexQueryTest()
        self._log("End of index query test. Normal time: avg= %.5fs, dev= %.5fs. CPU time: avg= %.5fs, dev= %.5fs." % (self.average, self.deviation, self.caverage, self.cdeviation))

        self._log("Starting remove conference test")
        self._removeConfTest()
        self._log("End of remove conference test. Normal time: avg= %.5fs, dev= %.5fs. CPU time: avg= %.5fs, dev= %.5fs." % (self.average, self.deviation, self.caverage, self.cdeviation))

        self._log("Starting random operations test")
        self._randomOpsTest()
        self._log("End of random operations test. Normal time: avg= %.5fs, dev= %.5fs. CPU time: avg= %.5fs, dev= %.5fs." % (self.average, self.deviation, self.caverage, self.cdeviation))

        self._log("End of tests")
        self._log('')
        assert True


######## Add booking test ########

    def _addBookingTest(self):
        def executeAddBookingTest():
            times = []
            i = 0
            while i < bookingsPerTest:
                confId = self._getConfIdForAdding()
                start = time.time()
                cstart = time.clock()
                self._addBooking(confId)
                cend = time.clock()
                end = time.time()
                times.append((end - start, cend - cstart))
                self._updateValidIdsAfterAddingBooking(confId)
                i = i + 1

            self.average, self.deviation, self.caverage, self.cdeviation = processResults(times)

        if doProfile:
            profile.runctx("executeAddBookingTest()", {}, {'executeAddBookingTest' : executeAddBookingTest}, 'addBooking.prof')
        else:
            exec "executeAddBookingTest()" in {}, {'executeAddBookingTest' : executeAddBookingTest}

    def _getConfIdForAdding(self):
        return self.random.choice(self.validConfIds)

    def _updateValidIdsAfterAddingBooking(self, confId):
        if confId not in self.confsWithBookings:
            self.confsWithBookings.append(confId)

    def _addBooking(self, confId):
        self.cdbmgr.startRequest()
        params = {"conference": confId,
                  "type": 'DummyPlugin',
                  "bookingParams": {"startDate": self._randomDate(startDate, endDate)},
                  }
        service = CollaborationCreateTestCSBooking(params)
        service._checkParams()
        service._getAnswer()
        self.cdbmgr.endRequest()

######## Remove booking test ########

    def _removeBookingTest(self):
        def executeRemoveBookingTest():
            times = []
            i = 0
            while i < bookingsPerTest:
                confId, bookingId = self._getIdsForRemoveBooking()

                start = time.time()
                cstart = time.clock()
                self._removeBooking(confId, bookingId)
                cend = time.clock()
                end = time.time()
                times.append((end - start, cend - cstart))

                self._updateValidIdsAfterRemoveBooking(confId)

                i = i + 1

            self.average, self.deviation, self.caverage, self.cdeviation = processResults(times)

        if doProfile:
            profile.runctx("executeRemoveBookingTest()", {}, {'executeRemoveBookingTest' : executeRemoveBookingTest}, 'removeBooking.prof')
        else:
            exec "executeRemoveBookingTest()" in {}, {'executeRemoveBookingTest' : executeRemoveBookingTest}

    def _getIdsForRemoveBooking(self):
        n = 0
        self.cdbmgr.startRequest()
        while n == 0:
            counter = 0
            confId = self.random.choice(self.confsWithBookings)
            testBookings = Catalog.getIdx("cs_bookingmanager_conference").get(confId)._bookingsByType.get("DummyPlugin", []) #list of booking ids
            n = len(testBookings)
            if n > 0:
                bookingId = self.random.choice(testBookings)
            else:
                counter += 1
                if counter > 100:
                    self.fail("Could not found a good conference for remove booking")
        self.cdbmgr.endRequest()
        return confId, bookingId

    def _updateValidIdsAfterRemoveBooking(self, confId):
        self.cdbmgr.startRequest()
        if len(Catalog.getIdx("cs_bookingmanager_conference").get(confId)._bookingsByType.get("DummyPlugin", [])) == 0:
            self.confsWithBookings.remove(confId)
        self.cdbmgr.endRequest()

    def _removeBooking(self, confId, bookingId):
        self.cdbmgr.startRequest()

        params = {"conference": confId,
                  "bookingId": bookingId
                  }
        service = CollaborationRemoveCSBooking(params)
        service._checkParams()
        service._getAnswer()
        self.cdbmgr.endRequest()

######## Remove conference test ########

    def _removeConfTest(self):
        def executeRemoveConfTest():
            self.removedConfs = set([''])
            times = []
            i = 0
            while i < removeConfsPerTest:

                confId = self.random.choice(self.confsWithBookings)

                start = time.time()
                cstart = time.clock()
                self._removeConf(confId)
                cend = time.clock()
                end = time.time()
                times.append((end - start, cend - cstart))
                i = i + 1

                self.validConfIds.remove(confId)
                self.confsWithBookings.remove(confId)

                if len(self.confsWithBookings) == 0:
                    self._log("Stopped removeConf test after removing " + str(i) + " conferences")
                    break

            self.average, self.deviation, self.caverage, self.cdeviation = processResults(times)

        if doProfile:
            profile.runctx("executeRemoveConfTest()", {}, {'executeRemoveConfTest' : executeRemoveConfTest}, 'removeConference.prof')
        else:
            exec "executeRemoveConfTest()" in {}, {'executeRemoveConfTest' : executeRemoveConfTest}

    def _removeConf(self, confId):
        self.cdbmgr.startRequest()
        Catalog.getIdx("cs_bookingmanager_conference").get(confId).notifyDeletion()
        self.cdbmgr.endRequest()

######## Index query test ########

    def _indexQueryTest(self):
        def executeIndexQueryTest():
            times = []
            i = 0
            while i < indexQueriesPerTest:
                start = time.time()
                cstart = time.clock()
                self._indexQuery()
                cend = time.clock()
                end = time.time()
                times.append((end - start, cend - cstart))
                i = i + 1

            self.average, self.deviation, self.caverage, self.cdeviation = processResults(times)

        if doProfile:
            profile.runctx("executeIndexQueryTest()", {}, {'executeIndexQueryTest' : executeIndexQueryTest}, 'indexQuery.prof')
        else:
            exec "executeIndexQueryTest()" in {}, {'executeIndexQueryTest' : executeIndexQueryTest}

    def _indexQuery(self):
        self.cdbmgr.startRequest()

        fromConfId = self.random.choice(self.validConfIds)
        toConfId = self.random.choice(self.validConfIds)
        if int(toConfId) < int(fromConfId):
            fromConfId, toConfId = toConfId, fromConfId
        fromTitle = ConferenceHolder().getById(fromConfId).getTitle()
        toTitle = ConferenceHolder().getById(toConfId).getTitle()

        params = {"page" : self.random.randint(0, 10),
                  "resultsPerPage" : 50,
                  "indexName": 'all',
                  "viewBy": 'conferenceTitle',
                  "orderBy": "descending",
                  "fromTitle": fromTitle,
                  "toTitle": toTitle,
                  "sinceDate": '',
                  "toDate": '',
                  "fromDays": '',
                  "toDays": '',
                  "onlyPending": False,
                  "categoryId": '',
                  "conferenceId": ''
                  }

        service = CollaborationBookingIndexQuery(params)
        service._checkParams()
        service._getAnswer()

        self.cdbmgr.endRequest()

######## Random ops test ########

    def _randomOpsTest(self):
        randomOps = ['removeConf'] + ['removeBooking']*2 + ['indexQuery']*3 + ['addBooking']*10
        timesRemoveConf = []
        timesRemoveBooking = []
        timesIndexQuery = []
        timesAddBooking = []

        i = 0
        while i < randomOpsPerTest:
            i = i + 1
            op = self.random.choice(randomOps)
            if op == 'removeConf':
                confId = self.random.choice(self.confsWithBookings)
                start = time.time()
                cstart = time.clock()
                self._removeConf(confId)
                cend = time.clock()
                end = time.time()
                timesRemoveConf.append((end - start, cend - cstart))
                self.validConfIds.remove(confId)
                self.confsWithBookings.remove(confId)
            elif op == 'removeBooking':
                confId, bookingId = self._getIdsForRemoveBooking()
                start = time.time()
                cstart = time.clock()
                self._removeBooking(confId, bookingId)
                cend = time.clock()
                end = time.time()
                timesRemoveBooking.append((end - start, cend - cstart))
                self._updateValidIdsAfterRemoveBooking(confId)
            elif op == 'indexQuery':
                start = time.time()
                cstart = time.clock()
                self._indexQuery()
                cend = time.clock()
                end = time.time()
                timesIndexQuery.append((end - start, cend - cstart))
            elif op == 'addBooking':
                confId = self._getConfIdForAdding()
                start = time.time()
                cstart = time.clock()
                self._addBooking(confId)
                cend = time.clock()
                end = time.time()
                timesAddBooking.append((end - start, cend - cstart))


        if timesAddBooking:
            self._log("[Random ops test] Add booking. Normal time: avg= %.5fs, dev= %.5fs. CPU time: avg= %.5fs, dev= %.5fs." % processResults(timesAddBooking))
        else:
            self._log("[Random ops test] No add booking operations were executed")

        if timesIndexQuery:
            self._log("[Random ops test] Index Query. Normal time: avg= %.5fs, dev= %.5fs. CPU time: avg= %.5fs, dev= %.5fs." % processResults(timesIndexQuery))
        else:
            self._log("[Random ops test] No index query operations were executed")

        if timesRemoveBooking:
            self._log("[Random ops test] Remove booking. Normal time: avg= %.5fs, dev= %.5fs. CPU time: avg= %.5fs, dev= %.5fs." % processResults(timesRemoveBooking))
        else:
            self._log("[Random ops test] No remove booking operations were executed")

        if timesRemoveConf:
            self._log("[Random ops test] Remove conference. Normal time: avg= %.5fs, dev= %.5fs. CPU time: avg= %.5fs, dev= %.5fs." % processResults(timesRemoveConf))
        else:
            self._log("[Random ops test] No remove conference operations were executed")

        self.average, self.deviation, self.caverage, self.cdeviation = processResults(timesAddBooking + timesAddBooking + timesAddBooking + timesAddBooking)


######## Logging and util stuff ########

    def _loggingSetup(self):
        self.logger = logging.getLogger('CollaborationTest')
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
        self.logger.addHandler(handler)

    def _log(self, message):
        self.logger.debug(str(message))

    def _randomDate(self, start, end):
        stime = time.mktime(time.strptime(start, dateFormat))
        etime = time.mktime(time.strptime(end, dateFormat))

        ptime = stime + self.random.random() * (etime - stime)

        return time.strftime(dateFormat, time.localtime(ptime))


######### Helper stuff ###########3
class FalseAction:
    def getOwner(self):
        return None

def processResults(data):
    n = len(data)
    sum = 0
    squareSum = 0
    csum = 0
    csquareSum = 0
    for t in data:
        sum += t[0]
        csum += t[1]
        squareSum += t[0] * t[0]
        csquareSum += t[1] * t[1]
    if n>0:
        average = sum / n
        caverage = csum / n
    else:
        average = 0
        caverage = 0
    if n > 1:
        deviation = math.sqrt((squareSum - n * average * average) / (n - 1))
        cdeviation = math.sqrt((csquareSum - n * caverage * caverage) / (n - 1))
    else:
        deviation = 0
        cdeviation = 0
    return average, deviation, caverage, cdeviation
