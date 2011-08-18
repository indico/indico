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

class CallForAbstractsTest(LoggedInSeleniumTestCase):
    def setUp(self):
        LoggedInSeleniumTestCase.setUp(self)

    def test_general_settings_test(self):
        sel = self._selenium
        sel.open("/confModifCFA.py?confId=74")
        sel.click("css=input.btn")
        sel.wait_for_page_to_load("30000")
        sel.click("css=div > input.btn")
        sel.wait_for_page_to_load("30000")
        sel.type("surname", "dummyuser")
        sel.type("firstname", "dummy")
        sel.click("action")
        sel.wait_for_page_to_load("30000")
        sel.click("selectedPrincipals")
        sel.click("//input[@value='select']")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Preview")
        sel.wait_for_page_to_load("30000")
        sel.click("link=List of Abstracts")
        sel.wait_for_page_to_load("30000")
        sel.click("newAbstract")
        sel.wait_for_page_to_load("30000")
        sel.type("title", "abstract1")
        sel.type("content", "abstract1")
        sel.click("addPrimAuthor")
        sel.wait_for_page_to_load("30000")
        sel.select("auth_prim_title", "label=Mr.")
        sel.type("auth_prim_family_name", "dummyuser")
        sel.type("auth_prim_first_name", "dummy")
        sel.type("auth_prim_email", "dummyuser2@dummz.org")
        sel.click("OK")
        sel.wait_for_page_to_load("30000")
        sel.click("//input[@value='<<back to the abstract list']")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Book of Abstracts Setup")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Reviewing")
        sel.wait_for_page_to_load("30000")
        sel.type("css=input[type=text]", "abstract?")
        sel.click("css=input.popUpButton")
        sel.click("link=Team")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Notification templates")
        sel.wait_for_page_to_load("30000")
        sel.click("css=form > input.btn")
        sel.wait_for_page_to_load("30000")
        sel.type("notificationTplTitle", "template")
        sel.type("notificationTplDescription", "template")
        sel.type("notificationTplAddress", "dummy@dummz.org")
        sel.type("notificationTplCCAddress", "dummyuser2@dummz.org")
        sel.type("notificationTplSubject", "gd")
        sel.type("notificationTplBody", "gaegter")
        sel.click("save")
        sel.click("submitter")
        sel.click("primaryAuthors")
        sel.click("save")
        sel.wait_for_page_to_load("30000")
        sel.click("css=li.tabUnselected")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Notification template list")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Setup")
        sel.wait_for_page_to_load("30000")
        sel.click("css=input.btn")
        sel.wait_for_page_to_load("30000")

    def tearDown(self):
        LoggedInSeleniumTestCase.tearDown(self)

if __name__ == "__main__":
    unittest.main()
