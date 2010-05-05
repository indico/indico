from MaKaC.common.db import DBMgr
from MaKaC.conference import ConferenceHolder
from MaKaC.errors import MaKaCError
from tests.BaseTest import BaseTest
from tests.Indicop import GridData
import unittest
from twill import commands as tc
from selenium import selenium
import unittest
from twill import commands as tc
from MaKaC.common.Configuration import Config

class SeleniumTestCase(unittest.TestCase, BaseTest):

    def setUp(self):
        self.verificationErrors = []
        self.confId = None
        self.selenium = None
        grid = GridData.getInstance()
        if grid.isActive():
            self.selenium = selenium(grid.getUrl(), grid.getPort(), grid.getEnv(), self.getRootUrl())
        else:
            self.selenium = selenium("localhost", 4444, "*chrome", self.getRootUrl())

        self.selenium.start()

        #Handy functions from selenium and twill you might need
        #set up the time between each selenium's commands (in milliseconds)
#        self.selenium.set_speed(5000)
        #convenient to set the browser in a known state
#        tc.clear_cookies()

    def tearDown(self):
        #if a confId is specified we'll try to delete the conf in case the test failed
        if self.confId:
            self.deleteConference(self.confId)


        self.selenium.stop()

        print "Errors array: %s" % self.verificationErrors
        self.assertEqual([], self.verificationErrors)

    def getRootUrl(self):
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