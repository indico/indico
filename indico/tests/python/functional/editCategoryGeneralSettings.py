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

class EditCategoryGeneralSettingsTest(LoggedInSeleniumTestCase):
    def setUp(self):
        LoggedInSeleniumTestCase.setUp(self)

    def test_general_settings_test(self):
        sel = self._selenium
        sel.open("/categoryModification.py?categId=0")
        sel.click("css=input.btn")
        sel.wait_for_page_to_load("30000")
        sel.type("name", "Sub-category")
        sel.type("description", "sub-category")
        sel.click("OK")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Sub-category")
        sel.wait_for_page_to_load("30000")
        sel.click("css=input.btn")
        sel.wait_for_page_to_load("30000")
        sel.select("visibility", "label=Sub-category")
        sel.click("OK")
        sel.wait_for_page_to_load("30000")
        sel.click("css=span.path > a")
        sel.wait_for_page_to_load("30000")
        sel.click("selectedCateg")
        sel.click("document.forms[2].elements[12]")
        sel.wait_for_page_to_load("30000")
        sel.click("confirm")
        sel.wait_for_page_to_load("30000")

    def tearDown(self):
        LoggedInSeleniumTestCase.tearDown(self)

if __name__ == "__main__":
    unittest.main()
