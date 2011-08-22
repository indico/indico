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
from indico.tests.python.functional.meeting_test import MeetingBase
import unittest, time, re, datetime


class ConferenceTests(MeetingBase, LoggedInSeleniumTestCase):
    def setUp(self):
        super(ConferenceTests, self).setUp(event='conference')

    def test_general_settings(self):
        super(ConferenceTests, self).test_general_settings()
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
        self.type(id="addContributionFocusField", text="treter")
        self.click(xpath="//input[@value='Add Existing']")
        self.type(id="userSearchFocusField", text="fake")

        self.click(css="div.searchUsersButtonDiv > input[type=button]")
        self.click(xpath="//ul[@id='_GID5']/li")
        self.click(css="div.popupButtonBar > div > div > input[type=button]")
        self.click(css="li.tabUnselected > span")
        self.click(xpath="//table[2]/tbody/tr/td[2]/div/div/div[2]/input[2]")
        self.select(xpath="//div[3]/div/div/table/tbody/tr/td[2]/div/select", label="Mr.")
        self.type(id="_GID7", text="Author")
        self.type(xpath="//div[3]/div/div/table/tbody/tr[3]/td[2]/div/input", text="Author")
        self.type(id="_GID8", text="author@dummz.org")
        self.click(css="a > input[type=button]")
        self.click(xpath="//div[3]/div/div/div/div/ul/li[3]/span")
        self.type(css="div.popUpTdContent > textarea", text="fdsfwfewfr")
        self.type(css="div.popUpTdContent > div > div > input[type=text]", text="ddd")
        self.click(css="div.popupButtonBar > input[type=button]")

    def test_programme(self):
        self.go("/confModifProgram.py?confId=0")
        self.click(css="input.btn")
        self.type(name="description", text="gfedger")
        self.click(name="Save")
        self.click(xpath="//input[@value='add track']")
        self.type(name="title", text="track 1")
        self.click(css="input.btn")
        self.click(name="selTracks")
        self.click(css="td > input.btn")

    def test_call_for_abstracts(self):
        self.go("/confModifCFA.py?confId=0")
        self.click(css="input.btn")
        self.click(css="div > input.btn")
        self.type(name="surname", text="fake")
        self.click(name="action")
        self.click(xpath="//input[@value='select']")
        self.click(ltext="Preview")
        self.click(ltext="List of Abstracts")
        self.click(name="newAbstract")
        self.type(name="title", text="abstract1")
        self.type(id="f_content", text="abstract1")
        self.click(name="addPrimAuthor")
        self.select(name="auth_prim_title", label="Mr.")
        self.type(name="auth_prim_family_name", text="dummyuser")
        self.type(name="auth_prim_first_name", text="dummy")
        self.type(name="auth_prim_email", text="dummyuser2@dummz.org")
        self.click(name="OK")
        self.click(xpath="//input[@value='<<back to the abstract list']")
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
        self.click(css="li.tabUnselected")
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
        self.click(css="li.tabUnselected")
        self.click(name="newRegistrant")
        self.type(name="*genfield*0-6", text="Geneva")
        self.select(name="*genfield*0-7", label="SWITZERLAND")
        self.select(name="arrivalDate", label="12-July-2011")
        self.select(name="departureDate", label="15-July-2011")
        self.click(xpath="//input[@name='accommodationType' and @value='own-accommodation']")
        self.click(css="input.btn")
        alert = self.get_alert()
        self.assertEqual("Are you sure you want to submit this form?", alert.text)
        alert.accept()
        self.go("/confModifRegistrationForm.py?confId=0")
        self.click(ltext="Preview")
        self.click(ltext="e-payment")
        self.click(css="input[type=submit]")
        self.click(css="form > input[type=submit]")
        self.type(name="specificConditionsPayment", text="some conditions here")
        self.click(css="input[type=submit]")
