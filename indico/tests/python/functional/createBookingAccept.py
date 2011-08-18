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

from seleniumTestCase import SeleniumTestCase
import unittest, time, re

class CreateBookingTest(SeleniumTestCase):
    def setUp(self):
        SeleniumTestCase.setUp(self)

    def test_general_settings_test(self):
        sel = self._selenium
        sel.open("/index.py")
        sel.click("css=strong")
        sel.wait_for_page_to_load("30000")
        sel.type("login", "dummyuser2")
        sel.type("password", "dummyuser2")
        sel.click("loginButton")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Room booking")
        sel.wait_for_page_to_load("30000")
        sel.click("roomLocation")
        sel.select("roomLocation", "label=Test 2")
        sel.click("css=td > input.btn")
        sel.wait_for_page_to_load("30000")
        sel.click("link=PRE-book")
        sel.wait_for_page_to_load("30000")
        sel.type("reason", "Lecture")
        sel.click("saveBooking")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Logout")
        sel.wait_for_page_to_load("30000")
        sel.click("css=strong")
        sel.wait_for_page_to_load("30000")
        sel.type("login", "dummyuser")
        sel.type("password", "dummyuser")
        sel.click("loginButton")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Server admin")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Rooms")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Configuration")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Test 2")
        sel.wait_for_page_to_load("30000")
        sel.click("css=input.btn")
        sel.wait_for_page_to_load("30000")
        sel.click("css=span.fakeLink")
        sel.click("//div[@id='roomBookingCal']/div[2]/div[2]/div/div[2]/div/div/p[2]")
        sel.wait_for_page_to_load("30000")
        sel.click("//input[@value='Accept']")
        self.failUnless(re.search, r"^Are you sure you want to ACCEPT this booking[\s\S]$", sel.get_confirmation())

    def tearDown(self):
        SeleniumTestCase.tearDown(self)

if __name__ == "__main__":
    unittest.main()
