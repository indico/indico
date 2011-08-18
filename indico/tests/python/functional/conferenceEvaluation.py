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

class EvaluationTest(LoggedInSeleniumTestCase):
    def setUp(self):
        LoggedInSeleniumTestCase.setUp(self)

    def test_general_settings_test(self):
        sel = self._selenium
        sel.open("/confModifEvaluation.py/setup?confId=62")
        sel.click("css=input.btn")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Edit")
        sel.wait_for_page_to_load("30000")
        sel.click("css=img[alt=Insert a question of type TextBox]")
        sel.wait_for_page_to_load("30000")
        sel.type("questionValue", "gergter")
        sel.type("keyword", "gerter")
        sel.click("save")
        sel.wait_for_page_to_load("30000")
        sel.click("css=img[alt=Insert a question of type TextArea]")
        sel.wait_for_page_to_load("30000")
        sel.type("questionValue", "awae")
        sel.type("keyword", "er")
        sel.click("save")
        sel.wait_for_page_to_load("30000")
        sel.click("css=img[alt=Insert a question of type PasswordBox]")
        sel.wait_for_page_to_load("30000")
        sel.type("questionValue", "erseq")
        sel.type("keyword", "j54r6")
        sel.click("save")
        sel.wait_for_page_to_load("30000")
        sel.click("css=img[alt=Insert a question of type Select]")
        sel.wait_for_page_to_load("30000")
        sel.type("keyword", u"oépiu")
        sel.type("questionValue", "h547")
        sel.type("choiceItem_1", "ghde")
        sel.type("choiceItem_2", "erte")
        sel.click("save")
        sel.wait_for_page_to_load("30000")
        sel.click("css=img[alt=Insert a question of type RadioButton]")
        sel.wait_for_page_to_load("30000")
        sel.type("keyword", "taear")
        sel.type("questionValue", "t34645n")
        sel.type("choiceItem_1", "ghdest")
        sel.type("choiceItem_2", "eat")
        sel.click("save")
        sel.wait_for_page_to_load("30000")
        sel.click("css=img[alt=Insert a question of type CheckBox]")
        sel.wait_for_page_to_load("30000")
        sel.type("questionValue", "htrwz")
        sel.type("keyword", "ghaewrt")
        sel.type("choiceItem_1", "aeger")
        sel.type("choiceItem_2", "gaetz")
        sel.click("save")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Preview")
        sel.wait_for_page_to_load("30000")
        sel.click("submit")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Results")
        sel.wait_for_page_to_load("30000")

    def tearDown(self):
        LoggedInSeleniumTestCase.tearDown(self)

if __name__ == "__main__":
    unittest.main()
