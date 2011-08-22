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

from seleniumTestCase import LoggedInSeleniumTestCase, setUpModule
from indico.tests.python.functional.lecture import LectureTests as LectureBase
import unittest, time, re, datetime

class MeetingTests(LectureBase):
    def setUp(self):
        super(MeetingTests, self).setUp(skip=True)
        self.go("/index.py")
        self.click(css="span.dropDownMenu")
        self.click(ltext="Create meeting")
        self.type(name="title", text="meeting test")
        self.click(id="advancedOptionsText")
        self.click(name="ok")

    def test_timetable(self):
        self.click(css="#inPlaceEditStartEndDate > div > div > span > div > a")
        sd = self.elem(xpath="//span[@id='inPlaceEditStartEndDate']/div/div/span/div/table/tbody/tr[1]/td[2]/div/input")
        sd.clear()
        sd.send_keys("11/07/2011 18:00")
        ed = self.elem(xpath="//span[@id='inPlaceEditStartEndDate']/div/div/span/div/table/tbody/tr[2]/td[2]/div/input")
        ed.clear()
        ed.send_keys("12/07/2011 18:00")

        self.click(css="button")

        self.go("/confModifSchedule.py?confId=0#20110711")
        self.click(ltext="Add new")
        self.click(ltext="Session")
        self.type(id="sessionTitle", text="Session 1")
        self.click(css="div.popupButtonBar > div > input[type=button]")
        self.click(ltext="Add new")
        self.click(ltext="Contribution")
        self.type(id="addContributionFocusField", text="Contrib 1")
        self.click(css="div.popupButtonBar > input[type=button]")
        self.click(ltext="Add new")
        self.click(ltext="Break")
        self.type(id="breakTitle", text="c")
        self.click(css="input[type=button]")
        self.click(css="li.tabUnselected")
        self.click(ltext="Add new")
        self.click(ltext="Session")
        self.click(ltext="Create a new session")
        self.type(id="sessionTitle", text="d")
        self.click(css="div.popupButtonBar > div > input[type=button]")
        self.click(xpath="//div[@id='timetableDiv']/div/div[2]/div/div/div/div[2]/div/span[3]")
        self.click(id="startTimeRescheduleRB")
        self.type(xpath="//div[2]/input", text="10")
        self.click(css="input[type=button]")
        self.click(xpath="//input[@value='OK']")

    def test_general_settings(self):
        super(MeetingTests, self).test_general_settings(lecture=False)
