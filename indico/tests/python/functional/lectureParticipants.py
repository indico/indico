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
        sel.open("/confModifParticipants.py?confId=45")
        sel.select("css=select", "label=not be sent")
        sel.wait_for_page_to_load("30000")
        sel.select("css=div > select", "label=displayed")
        sel.wait_for_page_to_load("30000")
        sel.select("document.forms[3].elements[0]", "label=may not apply")
        sel.wait_for_page_to_load("30000")
        sel.click("css=input.btn")
        sel.wait_for_page_to_load("30000")
        sel.type("surname", "dummy")
        sel.click("action")
        sel.wait_for_page_to_load("30000")
        sel.click("selectedPrincipals")
        sel.click("//input[@value='select']")
        sel.wait_for_page_to_load("30000")
        sel.click("//input[@value='Define new']")
        sel.wait_for_page_to_load("30000")
        sel.select("title", "label=Ms.")
        sel.type("surName", "New")
        sel.type("name", "Dummy")
        sel.type("email", "new@dummz.org")
        sel.click("ok")
        sel.wait_for_page_to_load("30000")
        sel.click("css=div.uniformButtonVBar > div > input.btn")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Participants list")
        sel.wait_for_page_to_load("30000")
        sel.click("//input[@name='participantsAction' and @value='Remove participant']")
        sel.wait_for_page_to_load("30000")

    def tearDown(self):
        LoggedInSeleniumTestCase.tearDown(self)

if __name__ == "__main__":
    unittest.main()
