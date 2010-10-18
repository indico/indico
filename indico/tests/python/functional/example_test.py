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

# For now, disable Pylint
# pylint: disable-all

import time, unittest
from seleniumTestCase import LoggedInSeleniumTestCase

class ExampleTest(LoggedInSeleniumTestCase):
    def setUp(self):
        LoggedInSeleniumTestCase.setUp(self)

    def testCreateDeleteLecture(self):
        sel = self._selenium

        # Start test
        sel.open("/indico//index.py")
        sel.click("//li[@id='createEventMenu']/span")
        sel.click("link=Create lecture")
        self.waitPageLoad(sel)
        sel.type("title", "lecture test")
        sel.click("advancedOptionsText")
        self.assertEqual("Default layout style", sel.get_text("//tr[@id='advancedOptions']/td/table/tbody/tr[2]/td[1]/span"))
        sel.click("advancedOptionsText")
        sel.click("ok")
        self.waitPageLoad(sel)

        #we set the confId, so in case the test fails, Teardown function is going to delete the conf
        LoggedInSeleniumTestCase.setConfID(self, sel.get_location())

        try: self.failUnless(sel.is_text_present, "lecture test")
        except AssertionError, e: self.verificationErrors.append(str(e))
        sel.click("link=Tools")
        self.waitPageLoad(sel)

        sel.click("link=Delete")
        self.waitPageLoad(sel)
        try: self.failUnless(sel.is_text_present, "Are you sure that you want to DELETE the conference \"lecture test\"?")
        except AssertionError, e: self.verificationErrors.append(str(e))
        sel.click("confirm")
        self.waitPageLoad(sel)


    def testConference(self):
        sel = self._selenium

        sel.open("/indico/index.py")
        sel.click("//li[@id='createEventMenu']/span")
        sel.click("link=Create conference")
        self.waitPageLoad(sel)
        sel.type("title", "conference test")
        sel.click("advancedOptionsText")
        try: self.failUnless(sel.is_text_present, "Description")
        except AssertionError, e: self.verificationErrors.append(str(e))
        sel.click("ok")
        self.waitPageLoad(sel)

        #we set the confId, so in case the test fails, Teardown function is going to delete the conf
        LoggedInSeleniumTestCase.setConfID(self, sel.get_location())

        sel.click("link=Timetable")
        self.waitPageLoad(sel)

        self.waitForElement(sel, "//a[text() = 'Add new']")
        sel.click("link=Add new")

        time.sleep(1)
        self.failUnless(sel.is_text_present, "Session")
        sel.click("link=Session")

        time.sleep(1)
        self.failUnless(sel.is_text_present, "Add Session")
        sel.type("//div[@class='popupWithButtonsMainContent']//input[@type='text']", "Session One")
        sel.type("//textarea", "bla bla bla")
        sel.click("//input[@value='Add']")

        time.sleep(1)
        self.failUnless(sel.is_text_present, "Session One")

        time.sleep(1)
        sel.click("//div[contains(@class,'timetableSession')]//div[1]")

        time.sleep(1)
        self.failUnless(sel.is_text_present, "View and edit this block timetable")

        sel.click("link=View and edit this block timetable")

        self.waitForElement(sel, "//a[text() = 'Add new']")
        sel.click("link=Add new")

        self.waitForElement(sel, "//a[text() = 'Contribution']")
        sel.click("link=Contribution")

        self.waitForAjax(sel, timeout=300000)
        self.waitForElement(sel, "//div[@class='title' and contains(text(), 'Add Contribution')]")


        sel.type("//div[@class='canvas']//input[@type='text']", "Contribution in Session One")
        sel.click("//div[@class='popupButtonBar']//input[@value='Add']")

        time.sleep(2)
        self.failUnless(sel.is_text_present, "Contribution in Session One")

        sel.click("link=Go back to timetable")
        self.failUnless(sel.is_text_present, "Session One")

        sel.click("link=Add new")
        self.failUnless(sel.is_text_present, "Break")
        sel.click("link=Break")
        time.sleep(1)

        self.failUnless(sel.is_text_present, "Add Break")
        sel.type("//div[@class='popupWithButtonsMainContent']//input[@type='text']", "Break in Contribution")
        sel.click("//input[@value='Add']")
        time.sleep(1)

        self.failUnless(sel.is_text_present, "Break in Contribution")


        sel.click("link=Tools")
        self.waitPageLoad(sel)
        sel.click("link=Delete")
        self.waitPageLoad(sel)
        try: self.failUnless(sel.is_text_present, "Are you sure that you want to DELETE the conference \"conference test\"?")
        except AssertionError, e: self.verificationErrors.append(str(e))
        sel.click("confirm")
        self.waitPageLoad(sel)

    def tearDown(self):
        LoggedInSeleniumTestCase.tearDown(self)

if __name__ == "__main__":
    unittest.main()
