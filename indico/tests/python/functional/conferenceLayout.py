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

class LayoutTest(LoggedInSeleniumTestCase):
    def setUp(self):
        LoggedInSeleniumTestCase.setUp(self)

    def test_general_settings_test(self):
        sel = self._selenium
        sel.open("/confModifDisplay.py/custom?confId=62")
        sel.click("link=Conference header")
        sel.wait_for_page_to_load("30000")
        sel.click("toggleSimpleTextButton")
        sel.wait_for_page_to_load("30000")
        sel.type("ttText", "Announcement")
        sel.click("savettText")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Menu")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Images")
        sel.wait_for_page_to_load("30000")

    def tearDown(self):
        LoggedInSeleniumTestCase.tearDown(self)

if __name__ == "__main__":
    unittest.main()
