# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

from seleniumTestCase import LoggedInSeleniumTestCase, setUpModule
from indico.tests.python.functional.lecture_test import LectureBase
import unittest, time, re, datetime

class MeetingBase(LectureBase):
    def setUp(self, event='meeting'):
        super(MeetingBase, self).setUp(event)

    def test_timetable(self):
        self.go("/event/0/manage/timetable/#20110711")
        self.click(ltext="Add new")
        self.click(ltext="Session")
        self.type(id="sessionTitle", text="Session 1")
        self.click(xpath="(//button[@type='button'])[5]")

        # wait for overlay to go away
        self.wait_remove(css='.ui-widget-overlay')
        self.wait_for_jquery()

        self.click(ltext="Add new")
        self.click(ltext="Contribution")
        self.type(id="addContributionFocusField", text="Contrib 1")
        self.click(xpath="(//button[@type='button'])[5]")

        # wait for overlay to go away
        self.wait_remove(css='.ui-widget-overlay')
        self.wait_for_jquery()

        self.click(ltext="Add new")
        self.click(ltext="Break")
        self.type(id="breakTitle", text="coffe break")
        self.click(xpath="(//button[@type='button'])[5]")

        self.wait_remove(css='.ui-widget-overlay')
        self.wait_for_jquery()

        self.click(css='.ui-tabs-nav li:nth-child(2)')

        self.click(ltext="Add new")
        self.click(ltext="Session")
        self.click(ltext="Create a new session")
        self.type(id="sessionTitle", text="Session 2")
        self.click(xpath="(//button[@type='button'])[5]")

        self.wait_remove(css='.ui-widget-overlay')
        self.wait_for_jquery()

        self.click(ltext="Reschedule")
        self.click(id="startTimeRescheduleRB")
        self.type(xpath="//div[2]/input", text="10")
        self.click(xpath="(//button[@type='button'])[5]")
        self.click(xpath="(//button[@type='button'])[8]")
        self.click(css="div.timetableBlock.timetableSession > div")
        self.click(ltext="Delete")
        alert = self.elem(css=".ui-dialog-content")
        self.assertEqual("Are you sure you want to delete this timetable entry?", alert.text)
        self.click(xpath="(//button[@type='button'])[5]")

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
