# -*- coding: utf-8 -*-
##
## $Id: testSciProgramme.py,v 1.3 2008/04/24 16:59:58 jose Exp $
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
import os
import unittest
import shutil
import sys
from subprocess import call, PIPE
from setup import confmerge

# CONFIG
DEBUG_INSTALL = True # set to True to see all stdout
# END CONFIG

TESTSITEPACKAGES = '_test_site_packages'
SAMPLE_MO_FILE = 'indico/MaKaC/po/locale/en_US/LC_MESSAGES/messages.mo'
MAKACCONFIGPY = "indico/MaKaC/common/MaKaCConfig.py"
MAKACCONFIGPYBAK = "%s.bak" % MAKACCONFIGPY
TESTCONFIGDIR = "_testconfigdir"
INDICOCONFCERNMARKER_START = '# DO NOT EDIT THIS LINE (CERN) ------------------------------------------------'
INDICOCONFCERNMARKER_END = '# DO NOT EDIT THIS LINE (CERN) - End of CERN specific'

class TestSetupPy(unittest.TestCase):
    def setUp(self):
        self._rootDir = os.path.join(os.path.dirname(__file__), '..')
        self._prevcwd = os.getcwd()
        os.chdir(self._rootDir)
        self._testFile = '%s/dist/cds-indico-None.tar.gz' % self._rootDir
        shutil.copyfile(MAKACCONFIGPY, MAKACCONFIGPYBAK)
        if os.path.exists(TESTCONFIGDIR):
            shutil.rmtree(TESTCONFIGDIR)

        if DEBUG_INSTALL:
            self._stdout = None
        else:
            self._stdout = PIPE

        self._stdin = PIPE

        if os.path.exists('indico/MaKaC/po/locale/en_US/LC_MESSAGES/messages.mo'):
            os.unlink('indico/MaKaC/po/locale/en_US/LC_MESSAGES/messages.mo')

        # Directory to uncompress packages to
        self.dist_test = '%s/dist_test' % self._rootDir


    def tearDown(self):
        shutil.copyfile(MAKACCONFIGPYBAK, MAKACCONFIGPY)

        for f in (self._testFile, 'indico/MaKaC/po/locale/en_US/LC_MESSAGES/messages.mo', MAKACCONFIGPYBAK):
            if os.path.exists(f):
                os.unlink(f)

        for dir in (self.dist_test, 'build', 'dist', os.path.join(self._rootDir, TESTSITEPACKAGES)):
            if os.path.exists(dir):
                shutil.rmtree(dir)

        os.chdir(self._prevcwd)


    def uncompressGeneratedDistFile(self):
        if os.path.exists(self.dist_test):
            shutil.rmtree(self.dist_test)

        os.makedirs(self.dist_test)
        self.assertEqual(0, call(['tar', 'xfz', 'dist/cds-indico-None.tar.gz', '-C', self.dist_test]))


    def testBuildShouldWork(self):
        self.assertEqual(0, call([sys.executable, 'setup.py', 'build'], stdout=self._stdout))


    def testInstallShouldWork(self):
        retcode = call([sys.executable, 'setup.py', 'install', '--force-upgrade', '--root', TESTSITEPACKAGES, '--config-dir', TESTCONFIGDIR, '--uid', str(os.getuid()), '--gid', str(os.getgid())], stdout=self._stdout, stdin=self._stdin)
        self.assertEqual(0, retcode)
        assert(os.path.exists('%s/indico.conf' % TESTCONFIGDIR))

    def testInstallDeveloperShouldWork(self):
        self.assertEqual(0, call([sys.executable, 'setup.py', 'install', '--uid', str(os.getuid()), '--gid', str(os.getgid()), '--developer'], stdout=self._stdout, stdin=self._stdin))


    def testSdistShouldWorkWithVersionSpecified(self):
        self.assertEqual(0, call([sys.executable, 'setup.py', 'sdist', '--version', '0.96'], stdout=self._stdout))
        self.assertTrue(os.path.exists(self._testFile))


    def testSdistCERNShouldPreserveCERNSpecificVariablesInIndicoConf(self):
        self.assertEqual(0, call([sys.executable, 'setup.py', 'sdist', '--version', '0.96', '--cern-package', '../cerndistdir'], stdout=self._stdout))
        self.uncompressGeneratedDistFile()
        self.assertNotEquals(-1, file('%s/dist_test/cds-indico-None/indico.conf' % self._rootDir).read().find(INDICOCONFCERNMARKER_START))
        self.assertNotEquals(-1, file('%s/dist_test/cds-indico-None/indico.conf' % self._rootDir).read().find(INDICOCONFCERNMARKER_END))

    def testSdistWithoutCERNShouldNotPreserverCERNSpecificVariablesInIndicoConf(self):
        self.testSdistShouldWorkWithVersionSpecified()
        self.uncompressGeneratedDistFile()
        self.assertEquals(-1, file('%s/dist_test/cds-indico-None/indico.conf' % self._rootDir).read().find(INDICOCONFCERNMARKER_START))
        self.assertEquals(-1, file('%s/dist_test/cds-indico-None/indico.conf' % self._rootDir).read().find(INDICOCONFCERNMARKER_END))


    def testInstallWithExistingInstallationShouldPreserveOldValuesInIndicoConf(self):
        self.testInstallShouldWork()
        # we modify installed indico.conf
        orig = file('%s/indico.conf' % TESTCONFIGDIR).read()
        self.assertNotEqual(-1, orig.find('("localhost", 9675)'))
        file('%s/indico.conf' % TESTCONFIGDIR, 'w').write(orig.replace('("localhost", 9675)', '("localhost", 9676)'))
        # print file('%s/indico.conf' % TESTCONFIGDIR).read()

        retcode = call([sys.executable, 'setup.py', 'install', '--force-upgrade', '--root', TESTSITEPACKAGES, '--config-dir', TESTCONFIGDIR, '--uid', str(os.getuid()), '--gid', str(os.getgid())], stdout=self._stdout, stdin=self._stdin)
        self.assertEqual(0, retcode)
        self.assertNotEqual(-1, file('%s/indico.conf' % TESTCONFIGDIR).read().find('(\'localhost\', 9676)'))

    def atestJsbuildShouldWork(self):
        self.assertEqual(0, call([sys.executable, 'setup.py', 'jsbuild'], stdout=self._stdout))
        self.assertTrue(os.path.exists(self._testFile))


    def testInstallDeveloperModeShouldCompileLanguages(self):
        assert(not os.path.exists('./indico/MaKaC/po/locale/en_US/LC_MESSAGES/messages.mo'))
        self.testInstallDeveloperShouldWork()
        assert(os.path.exists(SAMPLE_MO_FILE))


    def testInstallNonDeveloperShouldProperlySetMaKaCConfigReferenceToIndicoConf(self):
        self.testInstallShouldWork()
        from distutils.sysconfig import get_python_lib
        cfg_py = "%s/%s/%s" % (TESTSITEPACKAGES, get_python_lib()[1:], MAKACCONFIGPY.replace('indico/', ''))
        self.assertNotEquals(-1, (open(cfg_py).read().find("indico_conf = \"%s/indico.conf\"" % TESTCONFIGDIR)))


    def testInstallDeveloperShouldProperlySetMaKaCConfigReferenceToIndicoConf(self):
        self.testInstallDeveloperShouldWork()
        assert(open(MAKACCONFIGPY).read().find('indico_conf = "indico.conf"') != -1)