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

class ConferenceRegistrationTest(LoggedInSeleniumTestCase):
    def setUp(self):
        LoggedInSeleniumTestCase.setUp(self)

    def test_general_settings_test(self):
        sel = self._selenium
        sel.open("/confModifRegistrationForm.py?confId=62")
        sel.click("css=input.btn")
        sel.wait_for_page_to_load("30000")
        sel.click("//tr[2]/td/a/img")
        sel.wait_for_page_to_load("30000")
        sel.click("css=li.tabUnselected")
        sel.wait_for_page_to_load("30000")
        sel.click("newRegistrant")
        sel.wait_for_page_to_load("30000")
        sel.type("city", "dummy")
        sel.select("country", "label=SWITZERLAND")
        sel.select("arrivalDate", "label=12-July-2011")
        sel.select("departureDate", "label=15-July-2011")
        sel.click("//input[@id='accommodationType' and @value='own-accommodation']")
        sel.click("css=input.btn")
        self.failUnless(re.search, r"^Are you sure you want to submit this form[\s\S]$", sel.get_confirmation())
        sel.open("/confModifRegistrationForm.py?confId=62")
        sel.click("link=Preview")
        sel.wait_for_page_to_load("30000")
        sel.click("link=e-payment")
        sel.wait_for_page_to_load("30000")
        sel.click("css=input[type=submit]")
        sel.wait_for_page_to_load("30000")
        sel.click("css=form > input[type=submit]")
        sel.wait_for_page_to_load("30000")
        sel.type("specificConditionsPayment", "a")
        sel.click("css=input[type=submit]")
        sel.wait_for_page_to_load("30000")

    def tearDown(self):
        LoggedInSeleniumTestCase.tearDown(self)

if __name__ == "__main__":
    unittest.main()
