from MaKaC.common.db import DBMgr
from MaKaC import user
from MaKaC.common import indexes
from MaKaC.authentication import AuthenticatorMgr
from MaKaC.conference import ConferenceHolder
from MaKaC.errors import MaKaCError
from MaKaC.common import HelperMaKaCInfo
import unittest, time, re
from twill import commands as tc
import figleaf
from selenium import selenium
import unittest, time
import sys
import socket
from twill import commands as tc

class SeleniumTestCase(unittest.TestCase):
    
    def setUp(self):
        self.verificationErrors = []
        self.confId = None
        self.selenium = selenium("localhost", 4444, "*chrome", self.getRootUrl())
#        self.selenium = selenium("localhost", 4444, 'IE on Windows', self.getRootUrl())
        self.selenium.start()
        
        #Create dummy user and use this user to create conf, session and so on
        self.createDummyUser()
        
        #Handy functions from selenium and twill you might need
        #set up the time between each selenium's commands (in milliseconds)
#        self.selenium.set_speed(1000)
        #convenient to set the browser in a known state
#        tc.clear_cookies()
    
    def tearDown(self):
        #if a confId is specified we'll try to delete the conf in case the test failed
        if self.confId:
            self.deleteConference(self.confId)
        
        self.deleteDummyUser()
        
        self.selenium.stop()
        
        print "Errors array: %s" % self.verificationErrors
        self.assertEqual([], self.verificationErrors)
    
    
    def getRootUrl(self):
        #set this accordingly to your indico installation
        return "http://pcituds01/"
    
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
        id = self.ih.createIdentity( li, self.avatar, "Local" )
        self.ih.add( id )
        
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
        id=self.avatar.getIdentityList()[0]
        self.ih.removeIdentity(id)
        
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
        la.remove(id)
        self.ah.remove(self.avatar)
        
        DBMgr.getInstance().endRequest()
        
    def setConfID(self, url):
        #Parsing the url to retrieve the confId
        #if the confID is set up, we'll try to delete this conference in the teardown
        #in case the test fails
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