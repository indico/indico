import time
from seleniumTestCase import SeleniumTestCase

class ExampleTest(SeleniumTestCase):
    def setUp(self):
        SeleniumTestCase.setUp(self)

    def testCreateDeleteLecture(self):
        sel = self.selenium
        sel.open("/indico//index.py")
        sel.click("createEventLink")
        sel.click("link=Lecture")
        sel.wait_for_page_to_load("30000")
        sel.type("login", "dummyuser")
        sel.type("password", "dummyuser")
        sel.click("loginButton")
        sel.wait_for_page_to_load("30000")
        sel.type("title", "lecture test")
        sel.click("advancedOptionsText")
        self.assertEqual("Default layout style", sel.get_text("//tr[@id='advancedOptions']/td/table/tbody/tr[2]/td[1]/span"))
        sel.click("advancedOptionsText")
        sel.click("ok")
        sel.wait_for_page_to_load("30000")

        #we set the confId, so in case the test fails, Teardown function is going to delete the conf
        SeleniumTestCase.setConfID(self, sel.get_location())

        try: self.failUnless(sel.is_text_present("lecture test"))
        except AssertionError, e: self.verificationErrors.append(str(e))
        sel.click("link=Tools")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Delete")
        sel.wait_for_page_to_load("30000")
        try: self.failUnless(sel.is_text_present("Are you sure that you want to DELETE the conference \"lecture test\"?"))
        except AssertionError, e: self.verificationErrors.append(str(e))
        sel.click("confirm")
        sel.wait_for_page_to_load("30000")


    def testConference(self):
        sel = self.selenium
        sel.open("/indico/index.py")
        sel.click("//li[@id='createEventMenu']/span")
        sel.click("link=Create conference")
        sel.wait_for_page_to_load("30000")
        sel.type("login", "dummyuser")
        sel.type("password", "dummyuser")
        sel.click("loginButton")
        sel.wait_for_page_to_load("30000")
        sel.type("title", "conference test")
        sel.click("advancedOptionsText")
        try: self.failUnless(sel.is_text_present("Description"))
        except AssertionError, e: self.verificationErrors.append(str(e))
        sel.click("ok")
        sel.wait_for_page_to_load("30000")

        #we set the confId, so in case the test fails, Teardown function is going to delete the conf
        SeleniumTestCase.setConfID(self, sel.get_location())

        sel.click("link=Timetable")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Add new")

        time.sleep(1)
        self.failUnless(sel.is_text_present("Session"))
        sel.click("link=Session")

        time.sleep(1)
        self.failUnless(sel.is_text_present("Add Session"))
        sel.type("//div[@class='popupWithButtonsMainContent']//input[@type='text']", "Session One")
        sel.type("//textarea", "bla bla bla")
        sel.click("//input[@value='Add']")

        time.sleep(1)
        self.failUnless(sel.is_text_present("Session One"))

        time.sleep(1)
        sel.click("//div[contains(@class,'timetableSession')]//div[1]")

        time.sleep(1)
        self.failUnless(sel.is_text_present("View and edit this block timetable"))

        sel.click("link=View and edit this block timetable")
        sel.click("link=Add new")

        self.failUnless(sel.is_text_present("Contribution"))
        sel.click("link=Contribution")

        time.sleep(1)
        self.failUnless(sel.is_text_present("Add Contribution"))


        sel.type("//div[@class='canvas']//input[@type='text']", "Contribution in Session One")
        sel.click("//div[@class='popupButtonBar']//input[@value='Add']")

        time.sleep(5)
        self.failUnless(sel.is_text_present("Contribution in Session One"))

        sel.click("link=Go back to timetable")
        self.failUnless(sel.is_text_present("Session One"))

        sel.click("link=Add new")
        self.failUnless(sel.is_text_present("Break"))
        sel.click("link=Break")
        time.sleep(1)

        self.failUnless(sel.is_text_present("Add Break"))
        sel.type("//div[@class='popupWithButtonsMainContent']//input[@type='text']", "Break in Contribution")
        sel.click("//input[@value='Add']")
        time.sleep(1)

        self.failUnless(sel.is_text_present("Break in Contribution"))
        sel.click("link=Tools")

        sel.wait_for_page_to_load("30000")
        sel.click("//div[@class='eventActionsToolBarButtons']//a[3]")
        sel.wait_for_page_to_load("30000")

        self.failUnless(sel.is_text_present("Are you sure that you want to DELETE the conference \"conference test\"?"))

        sel.click("confirm")
        sel.wait_for_page_to_load("30000")

    def tearDown(self):
        SeleniumTestCase.tearDown(self)

if __name__ == "__main__":
    unittest.main()
