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

from seleniumTestCase import LoggedInSeleniumTestCase
import unittest, time, re

class MeetingTimetableTest(LoggedInSeleniumTestCase):
    def setUp(self):
        LoggedInSeleniumTestCase.setUp(self)

    def test_general_settings_test(self):
        sel = self._selenium
        sel.open("/confModifSchedule.py?confId=0#20110712")
        sel.click("link=Add new")
        sel.click("link=Session")
        for i in range(60):
            try:
                if sel.is_element_present("_GID8"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.type("_GID8", "a")
        sel.click("css=div.popupButtonBar > div > input[type=button]")
        sel.click("link=Add new")
        sel.click("link=Contribution")
        for i in range(60):
            try:
                if sel.is_element_present("addContributionFocusField"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.type("addContributionFocusField", "b")
        sel.click("css=div.popupButtonBar > input[type=button]")
        sel.click("link=Add new")
        sel.click("link=Break")
        for i in range(60):
            try:
                if sel.is_element_present("_GID20"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.type("_GID20", "c")
        sel.click("css=input[type=button]")
        sel.click("css=li.tabUnselected")
        sel.click("link=Add new")
        sel.click("link=Session")
        sel.click("link=Create a new session")
        for i in range(60):
            try:
                if sel.is_element_present("_GID28"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.type("_GID28", "d")
        sel.click("css=div.popupButtonBar > div > input[type=button]")
        sel.click("//div[@id='timetableDiv']/div/div[2]/div/div/div/div[2]/div/span[3]")
        sel.click("startTimeRescheduleRB")
        sel.type("_GID29", "10")
        sel.click("css=input[type=button]")
        sel.click("//input[@value='OK']")
        sel.wait_for_page_to_load("30000")

    def tearDown(self):
        LoggedInSeleniumTestCase.tearDown(self)

if __name__ == "__main__":
    unittest.main()
