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
import unittest, time, re


class LectureBase(object):

    def setUp(self, event='lecture'):
        super(LectureBase, self).setUp()
        self.go("/")
        self.click(css="span.dropDownMenu")
        self.click(ltext="Create %s" % event)
        self.type(name="title", text="%s test" % event)
        self.click(id="advancedOptionsText")
        self.click(name="ok")

        self.click(css="#inPlaceEditStartEndDate > div > div > span > div > a")
        sd = self.elem(xpath="//span[@id='inPlaceEditStartEndDate']/div/div/span/div/table/tbody/tr[1]/td[2]/div/input")
        sd.clear()
        sd.send_keys("11/07/2011 18:00")
        ed = self.elem(xpath="//span[@id='inPlaceEditStartEndDate']/div/div/span/div/table/tbody/tr[2]/td[2]/div/input")
        ed.clear()
        ed.send_keys("12/07/2011 18:00")
        self.click(css="button")
        self.wait_remove(css="#inPlaceEditStartEndDate > div > span")

    def test_tools(self):
        self.go("/event/0/manage/tools/")
        self.click(xpath="(//a[contains(text(),'Lock')])[2]")
        self.click(name="confirm")
        self.click(ltext="Unlock")
        self.click(ltext="Tools")
        self.click(ltext="Clone Event")
        self.click(css="input[name=cloneOnce]")
        self.click(name="confirm")
        self.go("/event/0/manage/tools/")
        self.click(ltext="Clone Event")
        self.type(css="#cloneIntervalPlace_until > div.dateField > input[type=text]", text="18/07/2011")
        self.click(name="cloneWithInterval")
        self.click(name="confirm")
        self.go("/event/0/manage/tools/")
        self.click(ltext="Clone Event")
        self.click(name="cloneGivenDays")
        alert = self.elem(css=".ui-dialog-content")
        self.assertEqual("The specified end date is not valid.", alert.text)
        self.click(css="button.ui-button")
        self.type(css="#cloneDaysPlace_until > div.dateField > input[type=text]", text="12/08/2011")
        box = self.elem(css="#cloneDaysPlace_start > div.dateField > input[type=text]")
        box.clear()
        box.send_keys("06/08/2011")
        self.click(name="cloneGivenDays")
        self.click(name="confirm")
        self.click(css="span.listName > a > span")
        self.wait(id='manageEventButton')
        self.click(id="manageEventButton")
        self.click(ltext="Tools")
        self.click(ltext="Delete")
        self.click(name="confirm")

    def test_general_settings(self, lecture=True):
        self.go("/event/0/manage/")
        self.click(ltext="(edit)")
        title = self.elem(css="input[type=text]")
        title.clear()
        title.send_keys("Test Event 1")
        self.click(css="button")
        self.click(css="#inPlaceEditDescription > div > div > span > div > a")
        self.type(css="textarea", text="whatever")
        self.click(css="button")
        self.click(css="#inPlaceEditLocation > span > a")
        self.type(css="input[type=text]", text="Some Place")
        self.type(name="_roomName", text="Room 1")
        self.type(css="textarea", text="some address")
        self.click(css="button")
        self.click(css="#inPlaceEditStartEndDate > div > div > span > div > a")
        sdate = self.elem(css="input[type=text]")
        sdate.clear()
        sdate.send_keys("14/07/2011 08:00")

        edate = self.elem(xpath="//span[@id='inPlaceEditStartEndDate']/div/div/span/div/table/tbody/tr[2]/td[2]/div/input")
        edate.clear()
        edate.send_keys("14/07/2011 09:00")

        self.click(css="button")
        self.click(css="#inPlaceEditSupport > div > div > span > div > a")
        supp = self.elem(xpath="//td[2]/input")
        supp.clear()
        supp.send_keys("Support 111")
        self.click(css="button")
        if lecture:
            self.click(css="#inPlaceEditOrganiserText > div > div > span > div > a")
            self.type(css="input[type=text]", text="Dummy")
            self.click(css="button")
        self.click(css="#inPlaceEditDefaultStyle > div > div > span > div > a")
        self.click(css="button")
        self.click(css="#inPlaceEditVisibility > div > div > span > div > a")
        self.select(css="#inPlaceEditVisibility select", label="Nowhere")
        self.click(css="button")
        self.click(css="#inPlaceEditType > div > div > span > div > a")
        self.click(css="button")
        self.click(css="#addNewChairLink")
        self.click(css="#addNew")
        self.select(css="div.popUpTdContent > select", label="Mr.")
        self.type(xpath="//td[2]/div/input", text="dummy")
        self.type(xpath="//tr[3]/td[2]/div/input", text="Dummy")
        self.type(xpath="//tr[5]/td[2]/div/input", text="new@dummz.org")
        self.click(css=".ui-dialog-buttonset button")

    def test_participants(self):
        self.go("/event/0/manage/participants/")
        self.click(css=".ui-tabs-nav li:nth-child(2)")
        self.click(ltext="Add")
        self.click(ltext="Indico User")
        self.type(id="userSearchFocusField", text="fake")
        self.click(css="input[type=\"button\"]")
        self.click(id="_GID1_existingAv0")
        self.click(xpath="(//button[@type='button'])[5]")

        # wait for overlay to go away
        self.wait_remove(css='.ui-widget-overlay')

        self.click(ltext="Add")
        self.click(ltext="New user")
        self.type(id="_GID3", text="Ficticio")
        self.type(id="_GID4", text="Joaquim")
        self.type(xpath="(//input[@type='text'])[3]", text="CERN")
        self.click(xpath="(//button[@type='button'])[5]")
        self.click(id="_GID5")
        self.type(id="_GID5", text="ficticio.joaquim@example.com")
        self.click(xpath="(//button[@type='button'])[5]")
        self.click(id="checkParticipant2")
        self.click(id="remove_users")

        self.wait_remove(css='#checkParticipant2')

        self.click(id="checkParticipant1")
        self.click(id="send_email")
        self.type(css="input[type=\"text\"]", text="test")
        self.click(xpath="(//button[@type='button'])[5]")

        @self.retry()
        def _retry():
            title = self.wait(css='.ui-dialog-title')
            self.assertTrue('E-mail sent' in title.text)

        _retry()

        self.click(css="button.ui-button")
        self.click(id="checkParticipant1")
        self.click(ltext="Manage attendance")
        self.click(ltext="Set as absent")
        self.wait(css='#checkParticipant1:not(:checked)')
        self.click(id="checkParticipant1")
        self.click(ltext="Manage attendance")

        time.sleep(0.5)

        button = self.elem(css="#excuse_absence")
        button.click()

    def test_evaluation(self):
        self.go("/event/0/manage/evaluation/setup/")
        self.click(ltext="Edit")
        self.click(xpath="//img[@alt='Insert a question of type TextBox']")
        self.type(name="questionValue", text="What is your name?")
        self.type(name="keyword", text="name")
        self.click(name="save")
        self.click(xpath="//img[@alt='Insert a question of type TextArea']")
        self.type(name="questionValue", text="What is your quest?")
        self.type(name="keyword", text="quest")
        self.click(name="save")
        self.click(xpath="//img[@alt='Insert a question of type PasswordBox']")
        self.type(name="questionValue", text="What is your password?")
        self.type(name="keyword", text="password")
        self.click(name="save")
        self.click(xpath="//img[@alt='Insert a question of type Select']")
        self.type(name="questionValue", text="What is your favorite color?")
        self.type(name="keyword", text="color")
        self.type(name="choiceItem_1", text="blue")
        self.type(name="choiceItem_2", text="yellow")
        self.click(name="save")
        self.click(xpath="//img[@alt='Insert a question of type RadioButton']")
        self.type(name="questionValue", text="I shall count to...")
        self.type(name="keyword", text="123")
        self.type(name="choiceItem_1", text="3")
        self.type(name="choiceItem_2", text="5")
        self.click(name="save")
        self.click(xpath="//img[@alt='Insert a question of type CheckBox']")
        self.type(name="questionValue", text="It is a...")
        self.type(name="keyword", text="a")
        self.type(name="choiceItem_1", text="witch")
        self.type(name="choiceItem_2", text="duck")
        self.click(name="save")
        self.click(ltext="Preview")
        self.click(name="submit")
        self.click(xpath="//li")
        self.click(css=".ui-tabs-nav li a")
        self.click(id="reinit")
        self.click(css="button.ui-button")
        self.click(css="div > input.btn")
        edate = self.elem(css="#eDatePlace > div.dateField > input[type=text]")
        edate.clear()
        edate.send_keys("21/7/2011")
        self.click(name="modify")

    def test_protection(self):
        self.go("/event/0/manage/access/")
        self.click(css="#inPlaceAddManagerButton")
        self.type(css="input#userSearchFocusField", text="fake")
        self.click(css=".searchUsersButtonDiv input")
        self.click(id="_GID1_existingAv0")
        self.click(css="button.ui-button")
        self.type(name="modifKey", text="123")
        self.click(id="setModifKey")
        alert = self.elem(css=".ui-dialog-content")
        self.assertEqual("Please note that it is more secure to make the event private instead of using a modification key.", alert.text)
        self.click(css="button.ui-button")
        self.click(name="changeToPrivate")
        self.type(id="accessKey", text="123")
        self.click(id="setAccessKey")
        alert = self.elem(css=".ui-dialog-content")
        self.assertEqual("Please note that it is more secure to make the event private instead of using an access key.", alert.text)
        self.click(css="button.ui-button")
        self.click(name="changeToPublic")
        self.click(name="changeToPrivate")


class LectureTests(LectureBase, LoggedInSeleniumTestCase):
    pass
