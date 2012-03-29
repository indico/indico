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
from indico.tests.python.functional.lecture_test import LectureBase
import unittest, time, re, datetime

class MeetingBase(LectureBase):
    def setUp(self, event='meeting'):
        super(MeetingBase, self).setUp(event)

    def test_timetable(self):
        self.go("/confModifSchedule.py?confId=0#20110711")
        self.click(ltext="Add new")
        self.click(ltext="Session")
        self.type(id="sessionTitle", text="Session 1")
        self.click(css="button.ui-button")
        self.click(ltext="Add new")
        self.click(ltext="Contribution")
        self.type(id="addContributionFocusField", text="Contrib 1")
        self.click(css="button.ui-button")
        self.click(ltext="Add new")
        self.click(ltext="Break")
        self.type(id="breakTitle", text="coffe break")
        self.click(css="button.ui-button")
        self.click(css="ul.ui-tabs-nav li:nth-child(2)")
        self.click(ltext="Add new")
        self.click(ltext="Session")
        self.click(ltext="Create a new session")
        self.type(id="sessionTitle", text="Session 2")
        self.click(css="button.ui-button")
        self.click(ltext="Reschedule")
        self.click(id="startTimeRescheduleRB")
        self.type(xpath="//div[2]/input", text="10")
        self.click(css="button.ui-button")
        self.click(xpath="(//button[@type='button'])[3]")
        self.click(css="div.timetableBlock.timetableSession > div")
        self.click(ltext="Delete")
        alert = self.get_alert()
        self.assertEqual("Are you sure you want to delete this timetable entry?", alert.text)
        alert.accept()

    def test_general_settings(self):
        super(MeetingBase, self).test_general_settings(lecture=False)

    def test_protection(self):
        super(MeetingBase, self).test_protection()

        self.click(css="input[type=button]")
        self.type(id="userSearchFocusField", text="fake")
        self.click(css="div.searchUsersButtonDiv > input[type=button]")
        self.click(id="_GID2_existingAv0")
        self.click(css="button.ui-button")
        self.click(xpath="//input[@value='Grant submission rights to all speakers']")
        self.click(xpath="//input[@value='Grant modification rights to all session conveners']")
        self.click(xpath="//input[@value='Remove all submission rights']")


class MeetingTests(MeetingBase, LoggedInSeleniumTestCase):
    pass
