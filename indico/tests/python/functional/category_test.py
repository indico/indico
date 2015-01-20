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


class CategoryTests(LoggedInSeleniumTestCase):

    def test_general_settings(self):
        self.go("/category/0/manage/")
        self.click(css="input.btn")
        self.type(name="name", text="Sub-category")
        self.type(name="description", text="sub-category")
        self.click(name="OK")
        self.click(ltext="Sub-category")
        self.click(css="input.btn")
        self.select(name="visibility", label="Sub-category")
        self.click(name="OK")
        self.click(css="span.path > a")
        self.click(name="selectedCateg")
        self.click(xpath="//input[@name='remove']")
        self.click(name="confirm")

    def test_protection(self):
        self.go("/category/0/manage/")
        self.click(css="input.btn")
        self.type(name="name", text="Sub-category")
        self.type(name="description", text="sub-category")
        self.click(name="OK")
        self.go("/category/1/manage/access")
        self.click(id="inPlaceAddManagerButton")
        self.type(id="userSearchFocusField", text="fake")
        self.click(xpath="//input[@value='Search']")
        self.click(id="_GID1_existingAv0")
        self.click(css="button.ui-button")
        time.sleep(1)
        self.click(name="changeToPublic")
        self.click(name="changeToPrivate")
        self.click(name="changeToInheriting")
        self.click(xpath="//input[@value='Add user']")
        self.type(id="userSearchFocusField", text="fake")
        self.click(xpath="//input[@value='Search']")
        self.click(id="_GID1_existingAv0")
        self.click(css="button.ui-button")
        self.type(name="notifyCreationList", text="dummy@dummz.org")
        self.click(xpath="//input[@value='save']")
