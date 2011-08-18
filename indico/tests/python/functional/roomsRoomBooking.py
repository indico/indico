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

class RoomsRoomBookingTest(LoggedInSeleniumTestCase):
    def setUp(self):
        LoggedInSeleniumTestCase.setUp(self)

    def test_general_settings_test(self):
        sel = self._selenium
        sel.open("/roomBooking.py/admin")
        sel.type("newLocationName", "Test 1")
        sel.click("css=input.btn")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Test 1")
        sel.wait_for_page_to_load("30000")
        sel.click("//input[@value='New Room']")
        sel.wait_for_page_to_load("30000")
        sel.type("name", "Room 1")
        sel.type("site", "1")
        sel.type("building", "1")
        sel.type("floor", "1")
        sel.type("roomNr", "1")
        sel.click("css=input[type=button]")
        for i in range(60):
            try:
                if sel.is_element_present("userSearchFocusField"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.type("userSearchFocusField", "")
        sel.type("userSearchFocusField", "d")
        sel.type("userSearchFocusField", "du")
        sel.type("userSearchFocusField", "d")
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
        sel.click("css=div.searchUsersButtonDiv > input[type=button]")
        sel.click("_GID1_existingAv0")
        sel.click("css=div.popupButtonBar > div > div > input[type=button]")
        sel.click("css=input.btn")
        sel.wait_for_page_to_load("30000")

    def tearDown(self):
        LoggedInSeleniumTestCase.tearDown(self)

if __name__ == "__main__":
    unittest.main()
