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

class MeetingToolsTest(LoggedInSeleniumTestCase):
    def setUp(self):
        LoggedInSeleniumTestCase.setUp(self)

    def test_general_settings_test(self):
        sel = self._selenium
        sel.open("/confModifTools.py/clone?confId=0")
        sel.click("//li[@onclick=\"window.location = 'http://localhost/conferenceModification.py/close?confId=0'\"]")
        sel.wait_for_page_to_load("30000")
        sel.click("confirm")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Unlock")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Tools")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Clone Event")
        sel.wait_for_page_to_load("30000")
        sel.click("css=input[name=cloneOnce]")
        sel.wait_for_page_to_load("30000")
        sel.click("confirm")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Tools")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Clone Event")
        sel.wait_for_page_to_load("30000")
        sel.click("//ul[@id='tabList']/li[5]")
        sel.wait_for_page_to_load("30000")
        sel.click("confirm")
        sel.wait_for_page_to_load("30000")
        sel.open("/confModifTools.py/clone?confId=0")
        sel.type("css=#cloneIntervalPlace_until > div.dateField > input[type=text]", "18/07/2011")
        sel.click("cloneWithInterval")
        sel.wait_for_page_to_load("30000")
        sel.click("confirm")
        sel.wait_for_page_to_load("30000")
        sel.open("/confModifTools.py/clone?confId=0")
        sel.type("css=#cloneDaysPlace_until > div.dateField > input[type=text]", "11/08/2011")
        sel.click("cloneGivenDays")
        sel.wait_for_page_to_load("30000")
        sel.click("confirm")
        sel.wait_for_page_to_load("30000")

    def tearDown(self):
        LoggedInSeleniumTestCase.tearDown(self)

if __name__ == "__main__":
    unittest.main()
