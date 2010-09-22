
from indico.tests.python.functional.seleniumTestCase import SeleniumTestCase
import unittest, time, re

class WSGIParallelConference_test(SeleniumTestCase):

    def setUp(self):
        SeleniumTestCase.setUp(self)

    def testConferenceTest(self):
        sel = self.selenium

        # Test fix - Login
        sel.open("/indico/signIn.py")
        sel.type("login", "dummyuser")
        sel.type("password", "dummyuser")
        sel.click("loginButton")
        sel.wait_for_page_to_load("30000")

        # Start test
        sel.open("/indico/index.py")
        sel.click("//div[1]/div[3]/div[2]/div/div[2]/div/div/ul/li/span[2]/a")
        sel.wait_for_page_to_load("30000")
        sel.click("manageEventButton")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Timetable")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Add new")
        sel.click("link=Session")
        sel.click("link=Create a new session")
        for i in range(60):
            try:
                if sel.is_element_present("_GID5"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("_GID5")
        sel.type("_GID5", "My session")
        sel.click("//input[@value='Add']")
        sel.click("//div[@id='timetableDiv']/div/div[2]/div/div/div[2]/div[2]/div[2]/div[1]/div")
        sel.click("link=View and edit this block timetable")
        for i in range(60):
            try:
                if "You are viewing the contents of the interval:" == sel.get_text("//div[@id='timetableDiv']/div/div[2]/div/div/div[1]/div[2]/div[2]/div/span"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("link=Add new")
        sel.click("link=Contribution")
        for i in range(60):
            try:
                if sel.is_element_present("addContributionFocusField"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.type("addContributionFocusField", "My contribution")
        sel.click("//div[4]/input[1]")
        sel.click("link=Add new")
        sel.click("link=Break")
        for i in range(60):
            try:
                if sel.is_element_present("_GID15"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.type("_GID15", "My break")
        sel.click("//input[@value='Add']")

    def tearDown(self):
        SeleniumTestCase.tearDown(self)

if __name__ == "__main__":
    unittest.main()
