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

"""
This module defines a base structure for Selenum test cases
"""

from functools import wraps

# Test libs
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
import unittest, time

# Indico
from indico.tests import BaseTestRunner
from indico.tests.config import TestConfig
from indico.tests.python.unit.util import IndicoTestCase

from indico.core.db import DBMgr
from indico.core.config import Config
from MaKaC.conference import ConferenceHolder
from MaKaC.errors import MaKaCError

import os


def setUpModule():
    global webd
    config = TestConfig.getInstance()
    browser = os.environ['INDICO_TEST_BROWSER']
    mode = os.environ['INDICO_TEST_MODE']
    server_url = os.environ.get('INDICO_TEST_URL')

    if mode == 'remote':
        capabilities = {
            'firefox': DesiredCapabilities.FIREFOX,
            'chrome': DesiredCapabilities.FIREFOX,
            'ie': DesiredCapabilities.INTERNETEXPLORER,
            'ipad': DesiredCapabilities.IPAD,
            'iphone': DesiredCapabilities.IPHONE,
            'android': DesiredCapabilities.ANDROID,
            'htmlunit': DesiredCapabilities.HTMLUNITWITHJS
            }
        cap = capabilities[browser]
        webd = webdriver.Remote(server_url, desired_capabilities=cap)
    else:
        drivers = {
            'firefox': webdriver.Firefox,
            'chrome': webdriver.Chrome,
            'ie': webdriver.Ie
            }

        webd = drivers[browser]();
    webd.implicitly_wait(25)


def elem_get(**kwargs):
    elem = None
    if 'id' in kwargs:
        elem = webd.find_element_by_id(kwargs['id'])
    elif 'xpath' in kwargs:
        elem = webd.find_element_by_xpath(kwargs['xpath'])
    elif 'name' in kwargs:
        elem = webd.find_element_by_name(kwargs['name'])
    elif 'css' in kwargs:
        elem = webd.find_element_by_css_selector(kwargs['css'])
    elif 'ltext' in kwargs:
        elem = webd.find_element_by_link_text(kwargs['ltext'])
    return elem


def name_or_id_target(f):
    def _wrapper(*args, **kwargs):
        elem = elem_get(**kwargs)
        for selector in ['css', 'ltext', 'name', 'xpath', 'id']:
            kwargs.pop(selector, None)
        return f(*(list(args) + [elem]), **kwargs)
    return _wrapper


class SeleniumTestCase(IndicoTestCase):
    """
    Base class for a selenium test case (grid or RC)
    """

    _requires = ['db.DummyUser']

    @classmethod
    def go(cls, rel_url):
        webd.get("%s%s" % (Config.getInstance().getBaseURL(), rel_url))

    @classmethod
    def failUnless(cls, func, *args):
        """
        failUnless that supports retries
        (1 per second)
        """
        triesLeft = 30
        exception = Exception()

        while (triesLeft):
            try:
                unittest.TestCase.failUnless(cls, func(*args))
            except AssertionError, e:
                exception = e
                triesLeft -= 1
                time.sleep(1)
                continue
            return
        raise exception

    @classmethod
    def get_alert(cls):
        alert = Alert(webd)
        return alert

    @classmethod
    @name_or_id_target
    def click(cls, elem):
        elem.click()

    @classmethod
    @name_or_id_target
    def type(cls, elem, text=''):
        elem.send_keys(text)

    @classmethod
    @name_or_id_target
    def blur(cls, elem):
        elem.send_keys(Keys.TAB)

    @classmethod
    @name_or_id_target
    def elem(cls, elem):
        return elem

    @classmethod
    def execute(cls, code):
        return webd.execute_script(code)

    @classmethod
    def jquery(cls, selector):
        return cls.execute("var elem = $('%s'); return elem?elem[0]:null;" % selector)

    @classmethod
    def wait_for_jquery(cls, timeout=5):
        WebDriverWait(webd, timeout).until(lambda s: s.execute_script("return jQuery.active == 0"))

    @classmethod
    @name_or_id_target
    def select(cls, elem, label=''):
        Select(elem).select_by_visible_text(label)

    @classmethod
    def wait(cls, timeout=5, **kwargs):
        """
        Wait for a given element to show up
        """
        return WebDriverWait(webd, timeout).until(lambda s: elem_get(webd=s, **kwargs))

    @classmethod
    def retry(cls, max_retries=2):
        def _retry(f):
            @wraps(f)
            def _wrapper():
                i = 0
                for i in range(0, max_retries):
                    try:
                        return f()
                    except:
                        time.sleep(1)
                raise Exception("'max_retries' exceeded")
            return _wrapper
        return _retry

    @classmethod
    def wait_remove(cls, css, timeout=5):
        ts = time.time()
        while True:
            if not cls.jquery(css):
                return

            time.sleep(1)

            if time.time() - ts > timeout:
                break

        raise Exception('timeout')

    @classmethod
    def tearDownClass(cls):
        webd.close()


class LoggedInSeleniumTestCase(SeleniumTestCase):

    def setUp(self):
        super(LoggedInSeleniumTestCase, self).setUp()

        # Login
        self.go("/user/login")
        self.type(name="login", text="dummyuser")
        self.type(name="password", text="dummyuser")
        self.click(id="loginButton")
