# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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
from indico.tests.python.functional.meeting_test import MeetingBase
import unittest, time, re, datetime


class ConferenceTests(MeetingBase, LoggedInSeleniumTestCase):
    def setUp(self):
        super(ConferenceTests, self).setUp(event='conference')

    def test_general_settings(self):
        super(ConferenceTests, self).test_general_settings()
        time.sleep(1)
        self.click(css="#inPlaceEditAdditionalInfo > div > div > span > div > a")
        self.type(css="textarea", text="some additional info")
        self.click(css="button")
        self.click(xpath="//input[@value='add']")
        self.type(name="ctName", text="Contribution type #1")
        self.type(name="ctDescription", text="a contribution type")
        self.click(name="save")

    def test_contributions(self):
        self.go("/confModifContribList.py?confId=0")
        self.click(css="td > form > input.btn")
        self.type(id="addContributionFocusField", text="contribution 1")
        self.click(xpath="//input[@value='Add Indico User']")
        self.type(id="userSearchFocusField", text="fake")
        self.click(xpath="//input[@value='Search']")
        self.click(id="_GID5_existingAv0")
        self.click(xpath="(//button[@type='button'])[3]")
        self.click(xpath="//li[2]/a/span")
        self.click(xpath="(//input[@value='Add Indico User'])[2]")
        self.type(id="userSearchFocusField", text="fake")
        self.click(xpath="//input[@value='Search']")
        self.click(id="_GID7_existingAv0")
        self.click(xpath="(//button[@type='button'])[3]")
        self.click(xpath="//button[@type='button']")
        self.click(name="contributions")
        self.click(xpath="(//input[@name='delete'])[2]")
        alert = self.get_alert()
        self.assertEqual("Are you sure you wish to delete the selected contributions?\nNote that you cannot undo this action.", alert.text)
        alert.accept()


    def test_programme(self):
        self.go("/confModifProgram.py?confId=0")
        self.click(css="input.btn")
        self.click(css="#inPlaceEditDescription > div > div > span > div > a")
        self.type(css="textarea", text="description text")
        self.click(xpath="//button[contains(text(), 'Save')]")
        self.click(xpath="//input[@value='add track']")
        self.type(name="title", text="track 1")
        self.click(xpath="//input[@value='ok']")
        self.click(name="selTracks")
        self.click(xpath="//input[@value='remove selected']")

    def test_call_for_abstracts(self):
        self.go("/confModifCFA.py?confId=0")
        self.click(css="input.btn")
        self.click(xpath="//input[@value='Add user']")
        self.type(id="userSearchFocusField", text="fake")
        self.click(css="div.searchUsersButtonDiv > input[type=button]")
        self.click(id="_GID1_existingAv0")
        self.click(css="button.ui-button")
        self.click(ltext="Preview")
        self.click(ltext="List of Abstracts")
        self.click(name="newAbstract")
        self.type(name="title", text="abstract1")
        self.type(id="f_content", text="abstract1")
        self.click(css="#inPlacePrAuthorsMenu a")
        self.click(css="a#defineNew.fakeLink")
        self.select(css="div.popUpTdContent select", label="Mr.")
        self.type(css="input#_GID1", text="dummyuser")
        self.type(css="input#_GID2", text="dummy")
        self.type(css="input#_GID3", text="dummy university")
        self.type(css="input#_GID4", text="dummyuser2@dummy.org")
        self.click(css="button.ui-button")
        self.click(name="validate")
        self.click(ltext="Book of Abstracts Setup")
        self.click(ltext="Reviewing")
        self.type(css="input[type=text]", text="abstract?")
        self.click(css="input.popUpButton")
        self.click(ltext="Team")
        self.click(ltext="Notification templates")
        self.click(css="form > input.btn")
        self.type(id="notificationTplTitle", text="template")
        self.type(id="notificationTplDescription", text="template")
        self.type(id="notificationTplAddress", text="dummy@dummz.org")
        self.type(id="notificationTplCCAddress", text="dummyuser2@dummz.org")
        self.type(id="notificationTplSubject", text="gd")
        self.type(id="notificationTplBody", text="gaegter")
        self.click(id="submitter")
        self.click(name="save")
        self.click(css="ul.ui-tabs-nav li")
        self.click(ltext="Notification template list")
        self.click(ltext="Setup")
        self.click(css="input.btn")

    def test_layout(self):
        self.go("/confModifDisplay.py/custom?confId=0")
        self.click(ltext="Conference header")
        self.click(id="toggleSimpleTextButton")
        self.type(name="ttText", text="Announcement")
        self.click(name="savettText")
        self.click(ltext="Menu")
        self.click(ltext="Images")

    def test_registration(self):
        self.go("/confModifRegistrationForm.py?confId=0")
        self.click(css="input.btn")
        self.click(xpath="//tr[2]/td/a/img")
        self.click(xpath="//tr[3]/td/a/img")
        self.click(css="ul.ui-tabs-nav li:nth-child(2) a")
        self.click(id="add_new_user")
        self.type(name="*genfield*0-6", text="Geneva")
        self.select(name="*genfield*0-7", label="SWITZERLAND")
        self.select(name="arrivalDate", label="12-July-2011")
        self.select(name="departureDate", label="15-July-2011")
        self.click(xpath="//input[@name='accommodationType' and @value='own-accommodation']")
        self.click(css="input.regFormButton[type=submit]")
        alert = self.get_alert()
        self.assertEqual("Are you sure you want to submit this form?", alert.text)
        alert.accept()
