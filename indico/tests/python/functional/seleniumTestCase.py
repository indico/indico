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

"""
This module defines a base structure for Selenum test cases
"""

# Test libs
from selenium import selenium
import unittest, time

# Indico
from indico.tests import BaseTestRunner
from indico.tests.runners import GridEnvironmentRunner

from MaKaC.common.db import DBMgr
from MaKaC.common.Configuration import Config
from MaKaC.conference import ConferenceHolder
from MaKaC.errors import MaKaCError


class SeleniumTestCase(unittest.TestCase, BaseTestRunner):
    """
    Base class for a selenium test case (grid or RC)
    """

    def setUp(self):
        self.verificationErrors = []
        self.confId = None
        sel = None

        gridData = GridEnvironmentRunner.getGridData()

        if gridData:
            sel = selenium(gridData.host,
                           gridData.port,
                           gridData.env,
                           self.getRootUrl())
        else:
            sel = selenium("localhost", 4444, "*firefox",
                           self.getRootUrl())

        sel.start()
        sel.window_maximize()

        # convenient to set the browser in a known state
        # from twill import commands as tc
        # tc.clear_cookies()

        # Handy functions from selenium and twill you might need
        # set up the time between each selenium's commands (in milliseconds)
        # self._selenium.set_speed(5000)

        self._selenium = sel

    def tearDown(self):
        #if a confId is specified we'll try to delete the conf
        # in case the test failed
        if self.confId:
            self.deleteConference(self.confId)

        self._selenium.stop()

        print "Errors array: %s" % self.verificationErrors
        self.assertEqual([], self.verificationErrors)

    def getRootUrl(self):
        """
        Return root URL of Indico instance
        """
        return Config.getInstance().getBaseURL()

    def setConfID(self, url):
        """
        Parsing the url to retrieve the confId
        if the confID is set up, we'll try to delete this conference in the teardown
        in case the test fails
        """

        splitUrl = url.split('=')
        self.confId = splitUrl[1]

    def deleteConference(self, confId):
        """
        Deletes a conference from the Indico DB
        """

        DBMgr.getInstance().startRequest()

        try:
            if confId:
                #we try to delete the conf
                ch = ConferenceHolder()
                conf = ch.getById(confId)
                conf.delete()
        except MaKaCError, e:
            #test succeeded and conf has already been deleted
            pass

        DBMgr.getInstance().endRequest()


    def waitForAjax(self, sel, timeout=5000):
        """
        Wait that all the AJAX calls finish
        """
        time.sleep(1)
        sel.wait_for_condition("selenium.browserbot.getCurrentWindow()"
                               ".activeWebRequests == 0", timeout)

    def waitForElement(self, sel, elem, timeout=5000):
        """
        Wait for a given element to show up
        """
        sel.wait_for_condition("selenium.isElementPresent(\"%s\")" % elem, timeout)

    def waitPageLoad(self, sel, timeout=30000):
        """
        Wait for a page to load (give it some time to load the JS too)
        """
        sel.wait_for_page_to_load(timeout)
        time.sleep(2)

    def failUnless(self, func, *args):
        """
        failUnless that supports retries
        (1 per second)
        """
        triesLeft = 30
        exception = Exception()

        while (triesLeft):
            try:
                unittest.TestCase.failUnless(self, func(*args))
            except AssertionError, e:
                print "left %d" % triesLeft
                exception = e
                triesLeft -= 1
                time.sleep(1)
                continue
            return

        raise exception

class LoggedInSeleniumTestCase(SeleniumTestCase):

    def setUp(self):

        super(LoggedInSeleniumTestCase, self).setUp()

        sel = self._selenium

        if not sel.is_text_present("Logout"):
            # Login
            sel.open("/indico/signIn.py")
            sel.type("login", "dummyuser")
            sel.type("password", "dummyuser")
            sel.click("loginButton")
            sel.wait_for_page_to_load("30000")



