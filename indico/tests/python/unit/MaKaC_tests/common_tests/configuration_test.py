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

# For now, disable Pylint
# pylint: disable-all

import unittest
from indico.tests.env import *

import shutil, sys
from indico.core.config import Config
from MaKaC.consoleScripts.installBase import modifyOnDiskIndicoConfOption


class _Needs_Rewriting_TestConfiguration(unittest.TestCase):
    def testGetInstanceShouldWork(self):
        self.config = Config.getInstance()

    def testDynamicFindersShouldWork(self):
        self.testGetInstanceShouldWork()
        self.config.getHtdocsDir()
        self.config.getVersion()

    def testSmtpUseTLS(self):
        self.testGetInstanceShouldWork()

        modifyOnDiskIndicoConfOption('etc/indico.conf.local', 'SmtpUseTLS', 'no')
        self.config.forceReload()
        self.assertEquals(False, self.config.getSmtpUseTLS())

        modifyOnDiskIndicoConfOption('etc/indico.conf.local', 'SmtpUseTLS', 'yes')
        self.config.forceReload()
        self.assertEquals(True, self.config.getSmtpUseTLS())


    def testReloadShoulShowNewIndicoConfValuesIfConfMoved(self):
        self.testGetInstanceShouldWork()
        orig = file('indico/MaKaC/common/MaKaCConfig.py').read()
        new = orig.replace('indico_conf = ""', 'indico_conf = "etc/indico2.conf"')
        file('indico/MaKaC/common/MaKaCConfig.py', 'w').write(new)
        try:
            shutil.move('etc/indico.conf.local', 'etc/indico2.conf')
            self.config.forceReload()
            self.config.getHtdocsDir()
        finally:
            file('indico/MaKaC/common/MaKaCConfig.py', 'w').write(orig)
            shutil.move('etc/indico2.conf', 'etc/indico.conf.local')


    def testReloadShoulShowNewIndicoConfValuesIfConfChanged(self):
        self.testGetInstanceShouldWork()
        orig = file('etc/indico.conf.local').read()
        file('etc/indico.conf.local', 'w').write(orig.replace('BaseURL              = "http://localhost/"',
                                                              'BaseURL              = "http://localhost2/"'))

        try:
            self.config.forceReload()
            self.assertEqual('http://localhost2/', self.config.getBaseURL())
        finally:
            file('etc/indico.conf.local', 'w').write(orig.replace('BaseURL              = "http://localhost2/"',
                                                                  'BaseURL              = "http://localhost/"'))
