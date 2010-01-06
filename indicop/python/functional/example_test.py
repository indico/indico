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
        self.assertEqual("Log in to Indico", sel.get_text("//div[3]/div[1]"))
        sel.type("login", "dummyuser")
        sel.type("password", "dummyuser")
        sel.click("loginButton")
        sel.wait_for_page_to_load("30000")
        #self.assertEqual("The lecture will take place in 1 2 3 4 5 6 7 8 9 date(s)", sel.get_text("//form[@id='eventCreationForm']/table[1]/tbody/tr[2]/td[2]")) not working in IE
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
        for i in range(60):
            try:
                if sel.is_text_present("Session"):
                    break
                else:
                    sel.click("link=Add new")
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("link=Session")
        for i in range(60):
            try:
                if sel.is_text_present("Add Session"):
                    break
                else:
                    sel.click("link=Session")
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.type("_GID5", "Session One")
        sel.type("//textarea", "bla bla bla")
        sel.click("//button[1]")
        for i in range(60):
            try:
                if sel.is_text_present("Session One"):
                    break
                else:
                    sel.click("//button[1]")
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("//div[@id='timetableDiv']/div/div[2]/div/div/div/div[2]/div[2]/div[2]/div/div/div[1]/div")
        for i in range(60):
            try:
                if sel.is_text_present("View and edit current interval timetable"):
                    break
                else:
                    sel.click("//div[@id='timetableDiv']/div/div[2]/div/div/div/div[2]/div[2]/div[2]/div/div/div[1]/div")
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("link=View and edit current interval timetable")
        sel.click("link=Add new")
        for i in range(60):
            try:
                if sel.is_text_present("Contribution"): break
                else: sel.click("link=Add new")
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("link=Contribution")
        for i in range(60):
            try:
                if sel.is_text_present("Add Contribution"): break
                else: sel.click("link=Contribution")
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.type("//input[@type='text']", "Contribution in Session One")
        sel.click("//button[1]")
        for i in range(60):
            try:
                if sel.is_text_present("Contribution in Session One"): break
                else: sel.click("//button[1]")
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("link=Go back to timetable")
        for i in range(60):
            try:
                if sel.is_text_present("Session One"): break
                else: sel.click("link=Go back to timetable")
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("link=Add new")
        for i in range(60):
            try:
                if sel.is_text_present("Break"): break
                else: sel.click("link=Add new")
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("link=Break")
        for i in range(60):
            try:
                if sel.is_text_present("Add Break"): break
                else: sel.click("link=Break")
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.type("//input[@type='text']", "Break")
        sel.click("//button[1]")
        for i in range(60):
            try:
                if sel.is_text_present("Break"): break
                else: sel.click("//button[1]")
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("link=Tools")
        sel.wait_for_page_to_load("30000")
        sel.click("//html/body/div[1]/div[4]/div/table/tbody/tr/td[2]/div/div/div/ul[@id='tabList']/li[5]/a")
        sel.wait_for_page_to_load("30000")
        for i in range(60):
            try:
                if sel.is_text_present("Are you sure that you want to DELETE the conference \"conference test\"?"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("confirm")
        sel.wait_for_page_to_load("30000")
        
    def tearDown(self):
        SeleniumTestCase.tearDown(self)

if __name__ == "__main__":
    unittest.main()
