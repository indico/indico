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

class ContributionsTest(LoggedInSeleniumTestCase):
    def setUp(self):
        LoggedInSeleniumTestCase.setUp(self)

    def test_general_settings_test(self):
        sel = self._selenium
        sel.open("/confModifContribList.py?confId=62")
        sel.click("css=td > form > input.btn")
        for i in range(60):
            try:
                if sel.is_element_present("addContributionFocusField"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.type("addContributionFocusField", "treter")
        sel.click("//input[@value='Add Existing']")
        for i in range(60):
            try:
                if sel.is_element_present("userSearchFocusField"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.type("userSearchFocusField", "")
        sel.type("userSearchFocusField", "d")
        sel.type("userSearchFocusField", "du")
        sel.type("userSearchFocusField", "dum")
        sel.type("userSearchFocusField", "dumm")
        sel.type("userSearchFocusField", "dummy")
        sel.type("userSearchFocusField", "dummy")
        sel.type("//tr[2]/td[2]/div/input", "")
        sel.type("//tr[2]/td[2]/div/input", "d")
        sel.type("//tr[2]/td[2]/div/input", "du")
        sel.type("//tr[2]/td[2]/div/input", "dum")
        sel.type("//tr[2]/td[2]/div/input", "dumm")
        sel.type("//tr[2]/td[2]/div/input", "dummy")
        sel.type("//td/div/table/tbody/tr[3]/td[2]/div/input", "")
        sel.type("//td/div/table/tbody/tr[3]/td[2]/div/input", "d")
        sel.type("//td/div/table/tbody/tr[3]/td[2]/div/input", "du")
        sel.type("//td/div/table/tbody/tr[3]/td[2]/div/input", "dum")
        sel.type("//td/div/table/tbody/tr[3]/td[2]/div/input", "dumm")
        sel.type("//td/div/table/tbody/tr[3]/td[2]/div/input", "dummy")
        sel.type("//td/div/table/tbody/tr[3]/td[2]/div/input", u"dummy¢")
        sel.type("//td/div/table/tbody/tr[3]/td[2]/div/input", "dummy")
        sel.type("//td/div/table/tbody/tr[3]/td[2]/div/input", "dummy@")
        sel.type("//td/div/table/tbody/tr[3]/td[2]/div/input", "dummy@d")
        sel.type("//td/div/table/tbody/tr[3]/td[2]/div/input", "dummy@du")
        sel.type("//td/div/table/tbody/tr[3]/td[2]/div/input", "dummy@dum")
        sel.type("//td/div/table/tbody/tr[3]/td[2]/div/input", "dummy@dumm")
        sel.type("//td/div/table/tbody/tr[3]/td[2]/div/input", "dummy@dummz")
        sel.type("//td/div/table/tbody/tr[3]/td[2]/div/input", "dummy@dummz.")
        sel.type("//td/div/table/tbody/tr[3]/td[2]/div/input", "dummy@dummz.o")
        sel.type("//td/div/table/tbody/tr[3]/td[2]/div/input", "dummy@dummz.or")
        sel.type("//td/div/table/tbody/tr[3]/td[2]/div/input", "dummy@dummz.org")
        sel.click("css=div.searchUsersButtonDiv > input[type=button]")
        sel.click("//ul[@id='_GID5']/li")
        sel.click("css=div.popupButtonBar > div > div > input[type=button]")
        sel.click("css=li.tabUnselected > span")
        sel.click("//table[2]/tbody/tr/td[2]/div/div/div[2]/input[2]")
        sel.select("//div[3]/div/div/table/tbody/tr/td[2]/div/select", "label=Mr.")
        sel.type("_GID7", "Author")
        sel.type("//div[3]/div/div/table/tbody/tr[3]/td[2]/div/input", "Author")
        sel.type("_GID8", "author@dummz.org")
        sel.click("css=a > input[type=button]")
        sel.click("//div[3]/div/div/div/div/ul/li[3]/span")
        sel.type("css=div.popUpTdContent > textarea", "fdsfwfewfr")
        sel.type("css=div.popUpTdContent > div > div > input[type=text]", "ddd")
        sel.click("css=div.popupButtonBar > input[type=button]")
        sel.wait_for_page_to_load("30000")

    def tearDown(self):
        LoggedInSeleniumTestCase.tearDown(self)

if __name__ == "__main__":
    unittest.main()
