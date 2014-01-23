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
import unittest, time, re, datetime

from indico.tests.python.unit.plugins_tests.RoomBooking_tests.roomblocking_test import RoomBooking_Feature
from indico.tests.python.unit.plugins import Plugins_Feature


class RoomBookingTests(LoggedInSeleniumTestCase):
    _requires = [RoomBooking_Feature, Plugins_Feature]

    def setUp(self):
        super(RoomBookingTests, self).setUp()

    def test_admin(self):
        self.go("/admin/rooms/locations/")
        self.type(name="newLocationName", text="Test 1")
        self.click(xpath="//input[@value='Add']")
        self.click(ltext="Test 1")
        self.click(xpath="//input[@value='New Room']")
        self.type(name="name", text="Room 1")
        self.type(name="site", text="1")
        self.type(name="building", text="1")
        self.type(name="floor", text="1")
        self.type(name="roomNr", text="1")
        self.click(css="input[type=button]")
        self.type(id="userSearchFocusField", text="fake")
        self.click(css="div.searchUsersButtonDiv > input[type=button]")
        self.click(id="_GID1_existingAv0")
        self.click(css="div.ui-dialog-buttonset > span > button[type=button]")
        self.click(css="input.btn")

    def test_assistance(self):
        self.go("/admin/plugins/type/RoomBooking/")
        self.type(name="RoomBooking.assistanceNotificationEmails", text="assistance@test.pl")
        self.click(xpath="//input[@value='Save settings']")
        self.go("/admin/rooms/locations/")
        self.type(name="newLocationName", text="TestUniverseAssistence1")
        self.click(xpath="//input[@value='Add']")
        self.click(ltext="TestUniverseAssistence1")
        self.click(xpath="//input[@value='New Room']")
        self.type(name="name", text="Room 1")
        self.type(name="site", text="1")
        self.type(name="building", text="1")
        self.type(name="floor", text="1")
        self.type(name="roomNr", text="1")
        self.click(name="resvNotificationAssistance")
        self.click(css="input[type=button]")
        self.type(id="userSearchFocusField", text="fake")
        self.click(css="div.searchUsersButtonDiv > input[type=button]")
        self.click(id="_GID1_existingAv0")
        self.click(css="div.ui-dialog-buttonset > span > button[type=button]")
        self.click(css="input.btn")
        self.go("/rooms/search/rooms?forNewBooking=True")
        self.select(name="roomName", label="TestUniverseAssistence1:   1-1-1 - Room 1")
        self.click(css="span#bookButtonWrapper > input[type=button]")
        self.type(name="reason", text="Test reason")
        self.click(name="needsAssistance")
        self.click(ltext="Book")
        self.wait_for_jquery()
        self.click(ltext="Modify")
        self.click(id="needsAssistance")
        self.click(ltext="Save")

    def test_create_accept_booking(self):
        # DB setup
        with self._context('database'):
            self._rooms[1].resvsNeedConfirmation = True
        # end

        self.go("/")
        self.click(css="li#userSettings a")
        self.click(ltext="Logout")
        self.click(ltext="Login")
        self.type(name="login", text="fake-1")
        self.type(name="password", text="fake-1")
        self.click(id="loginButton")
        self.click(ltext="Room booking")
        self.click(css="#roomselector li+li > label")
        self.click(ltext="Search")
        self.click(xpath="//div[@class='room-row'][1]/div[2]/div[2]")
        self.type(name="reason", text="Lecture")
        self.click(ltext="PRE-Book")
        self.click(css="li#userSettings a")
        self.click(ltext="Logout")
        self.click(css="strong")
        self.type(name="login", text="dummyuser")
        self.type(name="password", text="dummyuser")
        self.click(id="loginButton")
        self.click(ltext="Server admin")
        self.click(ltext="Rooms")
        self.click(ltext="Configuration")
        self.click(ltext="Universe")
        self.select(id="roomID", label="1-b-c - DummyRoom2")
        self.click(css="input.btn")
        self.wait(css="span.fakeLink")
        self.click(css="span.fakeLink")
        self.click(xpath="//div[@id='roomBookingCal']/div[2]/div[2]/div/div[2]/div/div/p[2]")
        self.click(ltext="Accept")
        alert = self.elem(css=".ui-dialog-content")
        self.assertEqual("Are you sure you want to accept this booking?", alert.text)
        self.click(css="button.ui-button")
