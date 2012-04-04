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
import unittest, time, re, datetime

from indico.tests.python.unit.plugins_tests.RoomBooking_tests.roomblocking_test import RoomBooking_Feature
from indico.tests.python.unit.plugins import Plugins_Feature

class RoomBookingTests(LoggedInSeleniumTestCase):
    _requires = [RoomBooking_Feature, Plugins_Feature]

    def setUp(self):
        super(RoomBookingTests, self).setUp()

    def test_admin(self):
        self.go("/roomBooking.py/admin")
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
        self.go("/adminPlugins.py?pluginType=RoomBooking")
        self.type(name="RoomBooking.assistanceNotificationEmails", text="assistance@test.pl")
        self.click(xpath="//input[@value='Save settings']")
        self.go("/roomBooking.py/admin")
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
        self.go("/roomBooking.py/search4Rooms?forNewBooking=True")
        self.select(name="roomName", label="TestUniverseAssistence1:   1-1-1 - Room 1")
        self.click(css="span#bookButtonWrapper > input[type=button]")
        self.type(name="reason", text="Test reason")
        self.click(name="needsAssistance")
        self.click(id="saveBooking")
        self.click(xpath="//input[@value='Modify']")
        self.click(name="needsAssistance")
        self.click(id="saveBooking")


    def test_create_accept_booking(self):
        # DB setup
        with self._context('database'):
            self._rooms[1].resvsNeedConfirmation = True
        # end

        self.go("/index.py")
        self.click(css="li#userSettings a")
        self.click(ltext="Logout")
        self.click(ltext="Login")
        self.type(name="login", text="fake-1")
        self.type(name="password", text="fake-1")
        self.click(id="loginButton")
        self.click(ltext="Room booking")
        self.click(name="roomLocation")
        self.select(name="roomLocation", label="Universe")
        self.click(css="td > input.btn")
        self.click(ltext="PRE-book")
        self.type(name="reason", text="Lecture")
        self.click(id="saveBooking")
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
        self.select(name="roomID", label="1-b-c - DummyRoom2")
        self.click(css="input.btn")
        self.click(css="span.fakeLink")
        self.click(xpath="//div[@id='roomBookingCal']/div[2]/div[2]/div/div[2]/div/div/p[2]")
        self.click(xpath="//input[@value='Accept']")
        alert = self.get_alert()
        self.assertEqual("Are you sure you want to ACCEPT this booking?", alert.text)
        alert.accept()
