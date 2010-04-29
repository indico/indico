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
import os
import unittest
import shutil
import sys
from subprocess import call, PIPE
from MaKaC.consoleScripts.installBase import modifyOnDiskIndicoConfOption

# CONFIG
DEBUG_INSTALL = True # set to True to see all stdout
# END CONFIG

TESTSITEPACKAGES = '_test_site_packages'
TESTCONFIGURATIONDIR = "_testinstall/etc"
TESTBINDIR = "_testinstall/bin"
TESTDOCUMENTATIONDIR = "_testinstall/doc"
TESTHTDOCSDIR = "_testinstall/htdocs"
SAMPLE_JSCOMPRESSED_FILE = 'indico/htdocs/js/presentation/pack/Presentation.pack.js'

SAMPLE_MO_FILE = 'indico/MaKaC/po/locale/en_US/LC_MESSAGES/messages.mo'
MAKACCONFIGPY = os.path.normpath("%s/../indico/MaKaC/common/MaKaCConfig.py" % os.path.dirname(__file__))
MAKACCONFIGPYBAK = os.path.normpath("%s.bak" % MAKACCONFIGPY)
INDICOCONFCERNMARKER_START = '# DO NOT EDIT THIS LINE (CERN) ------------------------------------------------'
INDICOCONFCERNMARKER_END = '# DO NOT EDIT THIS LINE (CERN) - End of CERN specific'
INDICOCONF = "%s/../etc/indico.conf.local" % os.path.dirname(__file__)

class TestSetupPy(unittest.TestCase):
    def setUp(self):
        self._rootDir = os.path.join(os.path.dirname(__file__), '..')
        self._prevcwd = os.getcwd()
        os.chdir(self._rootDir)
        self._testFile = '%s/dist/cds-indico-None.tar.gz' % self._rootDir
        self._testFileVersion = '%s/dist/cds-indico-0.96.tar.gz' % self._rootDir
        shutil.copyfile(MAKACCONFIGPY, MAKACCONFIGPYBAK)
        if os.path.exists(TESTCONFIGURATIONDIR):
            shutil.rmtree(TESTCONFIGURATIONDIR)

        if DEBUG_INSTALL:
            self._stdout = None
        else:
            self._stdout = PIPE

        self._stdin = PIPE

        for f in (SAMPLE_MO_FILE,
                  SAMPLE_JSCOMPRESSED_FILE):
            if os.path.exists(f):
                os.unlink(f)

        # Directory to uncompress packages to
        self.dist_test = '%s/dist_test' % self._rootDir

        # We make a backup of indico.conf
        shutil.copyfile(INDICOCONF, "%s.running_tests" % INDICOCONF)


    def tearDown(self):
        shutil.copyfile(MAKACCONFIGPYBAK, MAKACCONFIGPY)

        for f in (self._testFile, SAMPLE_MO_FILE, MAKACCONFIGPYBAK):
            if os.path.exists(f):
                os.unlink(f)

        for dir in (self.dist_test, 'build', 'dist', os.path.join(self._rootDir, TESTSITEPACKAGES), os.path.join(self._rootDir, '_testinstall')):
            if os.path.exists(dir):
                shutil.rmtree(dir)

        os.chdir(self._prevcwd)
        shutil.copyfile("%s.running_tests" % INDICOCONF, INDICOCONF)


    def uncompressGeneratedDistFile(self):
        if os.path.exists(self.dist_test):
            shutil.rmtree(self.dist_test)

        os.makedirs(self.dist_test)
        self.assertEqual(0, call(['tar', 'xfz', 'dist/cds-indico-0.96.tar.gz', '-C', self.dist_test]))


    def testBuildShouldWork(self):
        self.assertEqual(0, call([sys.executable, 'setup.py', 'build'], stdout=self._stdout))

    def testInstallShouldWork(self):
        modifyOnDiskIndicoConfOption('etc/indico.conf.local', 'ConfigurationDir', TESTCONFIGURATIONDIR)
        modifyOnDiskIndicoConfOption('etc/indico.conf.local', 'BinDir', TESTBINDIR)
        modifyOnDiskIndicoConfOption('etc/indico.conf.local', 'DocumentationDir', TESTDOCUMENTATIONDIR)
        modifyOnDiskIndicoConfOption('etc/indico.conf.local', 'HtdocsDir', TESTHTDOCSDIR)
        retcode = call([sys.executable, 'setup.py', 'install', '--root', TESTSITEPACKAGES, '--uid', str(os.getuid()), '--gid', str(os.getgid())], stdout=self._stdout, stdin=self._stdin)
        self.assertEqual(0, retcode)
        assert(os.path.exists('%s/indico.conf' % TESTCONFIGURATIONDIR))


    def testInstallDeveloperShouldWork(self):
        self.assertEqual(0, call([sys.executable, 'setup.py', 'develop'], stdout=self._stdout, stdin=self._stdin))


    def testSdistShouldWorkWithVersionSpecified(self):
        self.assertEqual(0, call([sys.executable, 'setup.py', 'sdist', '--version', '0.96'], stdout=self._stdout))
        self.assertTrue(os.path.exists(self._testFileVersion))


    def testInstallWithExistingInstallationShouldPreserveOldValuesInIndicoConf(self):
        self.testInstallShouldWork()
        # we modify installed indico.conf
        modifyOnDiskIndicoConfOption('%s/indico.conf' % TESTCONFIGURATIONDIR, 'DBConnectionParams', ("localhost", 9676))
        retcode = call([sys.executable, 'setup.py', 'install', '--force-upgrade', '--root', TESTSITEPACKAGES, '--uid', str(os.getuid()), '--gid', str(os.getgid())], stdout=self._stdout, stdin=self._stdin)
        self.assertEqual(0, retcode)
        self.assertNotEqual(-1, file('%s/indico.conf' % TESTCONFIGURATIONDIR).read().find('(\'localhost\', 9676)'))



    def testJsbuildShouldWork(self):
        self.assertEqual(0, call([sys.executable, 'setup.py', 'jsbuild'], stdout=self._stdout))
        self.assertTrue(os.path.exists(SAMPLE_JSCOMPRESSED_FILE))


    def testInstallDeveloperModeShouldCompileLanguages(self):
        assert(not os.path.exists(SAMPLE_MO_FILE))
        self.testInstallDeveloperShouldWork()
        assert(os.path.exists(SAMPLE_MO_FILE))


    def testInstallShouldProperlySetMaKaCConfigReferenceToIndicoConf(self):
        self.testInstallShouldWork()
        from distutils.sysconfig import get_python_lib
        cfg_py = "%s/%s" % (TESTSITEPACKAGES, 'usr/local/lib/python2.6/dist-packages/MaKaC/common/MaKaCConfig.py')
        print open(cfg_py).read()
        self.assertNotEquals(-1, (open(cfg_py).read().find("indico_conf = \"%s/indico.conf\"" % TESTCONFIGURATIONDIR)))


    def testInstallDeveloperShouldProperlySetMaKaCConfigReferenceToIndicoConf(self):
        self.testInstallDeveloperShouldWork()
        assert(open(MAKACCONFIGPY).read().find('indico_conf = ""') == -1)
