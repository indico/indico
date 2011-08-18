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

class MeetingGeneralSettingsTest(LoggedInSeleniumTestCase):
    def setUp(self):
        LoggedInSeleniumTestCase.setUp(self)

    def test_general_settings_test(self):
        sel = self._selenium
        sel.open("/conferenceModification.py?confId=0")
        sel.click("link=(edit)")
        sel.type("css=input[type=text]", "test meeting 21")
        sel.click("css=button")
        sel.click("css=#inPlaceEditDescription > div > div > span > div > a")
        sel.type("css=textarea", "g")
        sel.type("css=textarea", "gd")
        sel.type("css=textarea", "gdg")
        sel.type("css=textarea", "gdg")
        sel.click("css=button")
        sel.click("//td[@id='inPlaceEditLocation']/span[2]/a")
        sel.type("css=input[type=text]", "fd")
        sel.type("css=input[type=text]", "fd")
        sel.type("css=input[type=text]", "fds")
        sel.type("css=input[type=text]", "fds")
        sel.type("css=input[type=text]", "fds")
        sel.type("css=input[type=text]", "fds")
        sel.type("css=input[type=text]", "fds")
        sel.type("_roomName", "fs")
        sel.type("css=textarea", "ds")
        sel.type("css=textarea", "ds")
        sel.type("css=textarea", "ds")
        sel.click("css=button")
        sel.click("css=#inPlaceEditStartEndDate > div > div > span > div > a")
        sel.type("//span[@id='inPlaceEditStartEndDate']/div/div/span/div/table/tbody/tr[2]/td[2]/div/input", "1/07/2011 18:00")
        sel.type("//span[@id='inPlaceEditStartEndDate']/div/div/span/div/table/tbody/tr[2]/td[2]/div/input", "12/07/2011 18:00")
        sel.type("//span[@id='inPlaceEditStartEndDate']/div/div/span/div/table/tbody/tr[2]/td[2]/div/input", "12/07/2011 18:00")
        sel.click("css=button")
        sel.click("css=#inPlaceEditSupport > div > div > span > div > a")
        sel.type("_GID6", "test")
        sel.click("css=button")
        sel.type("_GID6", "")
        sel.click("css=button")
        sel.click("css=#inPlaceEditDefaultStyle > div > div > span > div > a")
        sel.click("css=button")
        sel.click("css=#inPlaceEditVisibility > div > div > span > div > a")
        sel.select("css=select", "label=blah")
        sel.click("css=button")
        sel.click("css=#inPlaceEditType > div > div > span > div > a")
        sel.click("css=button")
        sel.click("//input[@value='new']")
        sel.wait_for_page_to_load("30000")
        sel.select("title", "label=Mr.")
        sel.type("surName", "dummy")
        sel.type("name", "dummy")
        sel.click("ok")
        sel.wait_for_page_to_load("30000")

    def tearDown(self):
        LoggedInSeleniumTestCase.tearDown(self)

if __name__ == "__main__":
    unittest.main()
