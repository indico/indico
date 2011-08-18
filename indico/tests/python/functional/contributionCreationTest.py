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

class GeneralSettingsTest(LoggedInSeleniumTestCase):
    def setUp(self):
        LoggedInSeleniumTestCase.setUp(self)

    def test_general_settings_test(self):
        sel = self._selenium
        sel.open("/conferenceModification.py?confId=0")
        sel.click("link=Timetable")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Add new")
        sel.click("link=Contribution")
        for i in range(60):
            try:
                if sel.is_element_present("addContributionFocusField"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.type("addContributionFocusField", "test")
        sel.click("css=div.popupButtonBar > input[type=button]")
        sel.click("link=Add new")
        sel.click("link=Session")
        for i in range(60):
            try:
                if sel.is_element_present("_GID14"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.type("_GID14", "session 0")
        sel.click("css=div.popupButtonBar > div > input[type=button]")
        sel.click("css=div.timetableBlock.timetableContribution > div")
        sel.click("css=a.fakeLink > span")
        sel.click("//li[2]/input")
        sel.click("css=input[type=button]")
        sel.click("css=div.timetableBlock.timetableSession > div")
        for i in range(60):
            try:
                if sel.is_element_present("link=Delete"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("link=Delete")
        self.failUnless(re.search, r"^Are you sure you want to delete this timetable entry[\s\S]$", sel.get_confirmation())
    def tearDown(self):
        LoggedInSeleniumTestCase.tearDown(self)

if __name__ == "__main__":
    unittest.main()
