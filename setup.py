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

# Autoinstalls setuptools if the user doesn't have them already
import ez_setup
ez_setup.use_setuptools()

import commands
import getopt
import os
import re
import shutil
import string
import sys
from distutils.sysconfig import get_python_lib
from distutils.cmd import Command
from distutils.command import bdist

import pkg_resources
from setuptools.command import develop, install, sdist, bdist_egg, easy_install
from setuptools import setup, find_packages, findall

EXTRA_RESOURCES_URL = "http://cdswaredev.cern.ch/indico/wiki/Admin/Installation/IndicoExtras"

if sys.platform == 'linux2':
    import pwd
    import grp


class vars(object):
    '''Variable holder.'''
    packageDir = None
    versionVal = 'None'
    accessuser = None
    accessgroup = None
    dbInstalledBySetupPy = False
    binDir = None
    documentationDir = None
    configurationDir = None
    htdocsDir = None

###  Methods required by setup() ##############################################

def _generateDataPaths(x):

    dataFilesDict = {}

    for (baseDstDir, files, remove_first_x_chars) in x:
        for f in files:
            dst_dir = os.path.join(baseDstDir, os.path.dirname(f)[remove_first_x_chars:])
            if dst_dir not in dataFilesDict:
                dataFilesDict[dst_dir] = []
            dataFilesDict[dst_dir].append(f)

    dataFiles = []
    for k, v in dataFilesDict.items():
        dataFiles.append((k, v))

    return dataFiles

def _getDataFiles(x):
    """
    Returns a fully populated data_files ready to be fed to setup()

    WARNING: when creating a bdist_egg we need to include files inside bin,
    doc, config & htdocs into the egg therefore we cannot fetch indico.conf
    values directly because they will not refer to the proper place. We
    include those files in the egg's root folder.
    """

    # setup expects a list like this (('foo/bar/baz', 'wiki.py'),
    #                                 ('a/b/c', 'd.jpg'))
    #
    # What we do below is transform a list like this:
    #                                (('foo', 'bar/baz/wiki.py'),
    #                                 ('a', 'b/c/d.jpg'))
    #
    # first into a dict and then into a pallatable form for setuptools.

    # This re will be used to filter out etc/*.conf files and therefore not overwritting them
    isAConfRe = re.compile('etc\/[^/]+\.conf$')

    dataFiles = _generateDataPaths((('bin',           findall('bin'), 4),
                                    ('doc', findall('doc'), 4),
                                    ('etc', [xx for xx in findall('etc') if not isAConfRe.search(xx)], 4),
                                    ('htdocs',        findall('indico/htdocs'), 14)))
    return dataFiles





def _getInstallRequires():
    '''Returns external packages required by Indico

    These are the ones needed for runtime.'''

    base =  ['pytz', 'zope.index', 'zope.interface', 'simplejson', 'suds', 'cds-indico-extras']
    if sys.version_info[1] < 5: #for Python older than 2.5
        base.append('hashlib') # hashlib isn't a part of Python older than 2.5
        base.append('ZODB3>=3.8,<3.9.0a')
    else:                       #for Python 2.5+
        base.append('ZODB3>=3.8')

    return base


def _versionInit():
        '''Retrieves the version number from indico/MaKaC/__init__.py and returns it'''

        import datetime
        from indico.MaKaC import __version__
        v = __version__

        print('Version being packaged: %s' % v)

        return v

###  Commands ###########################################################
class sdist_indico(sdist.sdist):
    user_options = sdist.sdist.user_options + \
                   [('version=', None, 'version to distribute')]
    version = 'dev'

    def run(self):
        global x
        sdist.sdist.run(self)


class jsdist_indico:
    def jsCompress(self):
        from MaKaC.consoleScripts.installBase import jsCompress
        jsCompress()
        self.dataFiles += _generateDataPaths([('htdocs/js/presentation/pack', findall('indico/htdocs/js/presentation/pack'), 35),
                                             ('htdocs/js/indico/pack', findall('indico/htdocs/js/indico/pack'), 29)])


def _bdist_indico(dataFiles):
    class bdist_indico(bdist.bdist, jsdist_indico):
        def run(self):
            self.jsCompress()
            compileAllLanguages()
            bdist.bdist.run(self)

    bdist_indico.dataFiles = dataFiles
    return bdist_indico

def _bdist_egg_indico(dataFiles):
    class bdist_egg_indico(bdist_egg.bdist_egg, jsdist_indico):
        def run(self):
            self.jsCompress()
            compileAllLanguages()
            bdist_egg.bdist_egg.run(self)

    bdist_egg_indico.dataFiles = dataFiles
    return bdist_egg_indico

class jsbuild(Command):
    description = "minifies and packs javascript files"
    user_options = []
    boolean_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from MaKaC.consoleScripts.installBase import jsCompress
        jsCompress()

class fetchdeps:
    def run(self):
        print "Checking if dependencies need to be installed..."

        wset = pkg_resources.working_set

        wset.resolve(map(pkg_resources.Requirement.parse, _getInstallRequires()),
                           installer = self._installMissing)

        print "Done!"


    def _installMissing(self, dist):
        env = pkg_resources.Environment()
        print dist, EXTRA_RESOURCES_URL
        easy_install.main(["-f", EXTRA_RESOURCES_URL, "-U", str(dist)])
        env.scan()
        return env[str(dist)][0]


class fetchdeps_indico(fetchdeps, Command):
    description = "fetch all the dependencies needed to run Indico"
    user_options = []
    boolean_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


class develop_indico(Command):
    description = "prepares the current directory for Indico development"
    user_options = []
    boolean_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):

        fetchdeps().run()

        local = 'etc/indico.conf'
        if os.path.exists(local):
            print 'Upgrading existing etc/indico.conf..'
            upgrade_indico_conf(local, 'etc/indico.conf.sample')
        else:
            print 'Creating new etc/indico.conf..'
            shutil.copy('etc/indico.conf.sample', local)

        for f in [x for x in ('etc/zdctl.conf', 'etc/zodb.conf') if not os.path.exists(x)]:
            shutil.copy('%s.sample' % f, f)

        print """\nIndico needs to store some information in the filesystem (database, cache, temporary files, logs...)
Please specify the directory where you'd like it to be placed.
(Note that putting it outside of your sourcecode tree is recommended)"""
        prefixDir = raw_input('[%s]: ' % os.getcwd()).strip()

        if prefixDir == '':
            prefixDir = os.getcwd()

        directories = dict((d, os.path.join(prefixDir, d)) for d in
                           ['db', 'log', 'tmp', 'cache', 'archive'])

        print 'Creating directories...',
        for d in directories.values():
            if not os.path.exists(d):
                os.makedirs(d)
        print 'Done!'

        directories['htdocs'] = os.path.join(os.getcwd(), 'indico', 'htdocs')
        directories['bin'] = os.path.join(os.getcwd(), 'bin')
        directories['etc'] = os.path.join(os.getcwd(), 'etc')
        directories['doc'] = os.path.join(os.getcwd(), 'doc')

        self._update_conf_dir_paths(local, directories)

        from MaKaC.consoleScripts.installBase import _databaseText, _findApacheUserGroup, _checkDirPermissions, _updateDbConfigFiles, _updateMaKaCEggCache

        user = ''

        sourcePath = os.getcwd()

        if sys.platform == "linux2":
            # find the apache user/group
            user, group = _findApacheUserGroup(None, None)
            _checkDirPermissions(directories, dbInstalledBySetupPy = directories['db'], accessuser = user, accessgroup = group)

        _updateDbConfigFiles(directories['db'], directories['log'], os.path.join(sourcePath, 'etc'), directories['tmp'], user)

        _updateMaKaCEggCache(os.path.join(os.path.dirname(__file__), 'indico', 'MaKaC', '__init__.py'), directories['tmp'])

        updateIndicoConfPathInsideMaKaCConfig(os.path.join(os.path.dirname(__file__), ''), 'indico/MaKaC/common/MaKaCConfig.py')
        compileAllLanguages()
        print '''
%s
        ''' % _databaseText('etc')

    def _update_conf_dir_paths(self, filepath, dirs):
        fdata = open(filePath).read()
        for dir in dirs.items():
            d = dir[1].replace("\\","/") # For Windows users
            fdata = re.sub('\/opt\/indico\/%s'%dir[0], d, fdata)
        open(filePath, 'w').write(fdata)

class test_indico(Command):
    """
    Test command for Indico
    """

    description = "Test Suite Framework"
    user_options = [('specify=', None, "Use nosetests style (file.class:testcase)"),
                    ('coverage', None, "Output coverage report in html"),
                    ('unit', None, "Run only Unit tests"),
                    ('functional', None, "Run only Functional tests"),
                    ('pylint', None, "Run python source analysis"),
                    ('jsunit', None, "Run js unit tests"),
                    ('jslint', None, "Run js source analysis"),
                    ('jscoverage', None, "Output coverage report in html for js"),
                    ('jsspecify=', None, "Use js-test-driver style (TestCaseName.testName)"),
                    ('grid', None, "Use Selenium Grid"),
                    ('html', None, "Make an HTML report (when possible)"),
                    ('full-output', None, "Write the results to the console, in addition to the log file")]
    boolean_options = []

    specify = None
    coverage = False
    unit = False
    functional = False
    pylint = False
    jsunit = False
    jslint = False
    jscoverage = False
    jsspecify = None
    grid = None
    full_output = None
    html = None

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):

        if not self.checkIndicopPackages():
            print "Please install those missing packages before launching the tests again"
            sys.exit(-1)

        #missing jars will be downloaded automatically
        if not self.checkIndicopJars():
            print "Some jars could not be downloaded. Please download the missing jars manually"
            sys.exit(-1)

        from indico.tests import TestManager, TEST_RUNNERS
        testsToRun = []

        allTests = TEST_RUNNERS.keys()

        for testType in allTests:
            if getattr(self, testType):
                testsToRun.append(testType)

        if self.jsspecify and 'jsunit' not in testsToRun:
            testsToRun.append('jsunit')
        if self.specify != None and 'specify' not in testsToRun:
            testsToRun.append('specify')

        if testsToRun == []:
            testsToRun = allTests


        options = {'verbose': self.full_output,
                   'html': self.html,
                   'specify': self.specify,
                   'coverage': self.coverage}

        #this variable will tell what to do with the databases
        fakeDBPolicy = self.checkDBStatus(testsToRun, self.specify)

        manager = TestManager()
        result = manager.main(fakeDBPolicy, testsToRun, options)

        print result


    def checkDBStatus(self, testsToRun, specify):
        from indico.tests import TestConfig
        from indico.tests.util import TestZEOServer
        from MaKaC.common.Configuration import Config

        fakeDBPolicy = 0
        if ('functional' in testsToRun) or ('grid' in testsToRun) or ((specify != None) and (specify.find('unit/') < 0)):

            #checking if production db is running
            server = TestZEOServer(Config.getInstance().getDBConnectionParams()[1], 'test')
            if server.server.can_connect(server.options.family, server.options.address):
                print """Your production database is currently running.
Do you want to stop it using this command '%s' and run the tests?
(We will restart your produduction after the tests with this command '%s')""" % \
(TestConfig.getInstance().getStopDBCmd(), TestConfig.getInstance().getStartDBCmd())

                userInput = raw_input("Press enter or type 'yes' to accept: ")
                if userInput == 'yes' or userInput == '':
                    fakeDBPolicy = 3
                else:
                    print "Exiting testing framework..."
                    sys.exit(1)

            else:
                fakeDBPolicy = 2
        elif 'unit' in testsToRun or 'specify' in testsToRun:
            fakeDBPolicy = 1

        return fakeDBPolicy

    def checkIndicopPackages(self):
        packagesList = ['figleaf',
                        'nose',
                        'selenium',
                        'twill']
        validPackages = True

        for package in packagesList:
            try:
                pkg_resources.require(package)
            except pkg_resources.DistributionNotFound:
                print """
%s not found! Please install it.
i.e. try 'easy_install %s'""" % (package, package)
                validPackages = False
        return validPackages

    def checkIndicopJars(self):
        from indico.tests import TestConfig

        """check if needed jars are here, if not, dowloading them and unzip a file if necessary"""
        jarsList = {}
        currentFilePath = os.path.dirname(__file__)
        testModPath = os.path.join(currentFilePath, 'indico', 'tests')

        try:
            jarsList['jsunit'] = {'path':     os.path.join(testModPath,
                                                           'javascript',
                                                           'unit'),
                                  'url':      TestConfig.getInstance().getJsunitURL(),
                                  'filename': TestConfig.getInstance().getJsunitFilename()}

            jarsList['jscoverage'] = {'path':     os.path.join(testModPath,
                                                               'javascript',
                                                               'unit',
                                                               'plugins'),
                                      'url':      TestConfig.getInstance().getJscoverageURL(),
                                      'filename': TestConfig.getInstance().getJscoverageFilename()}

            jarsList['selenium'] = {'path':      os.path.join(testModPath,
                                                              'python',
                                                              'functional'),
                                    'url':       TestConfig.getInstance().getSeleniumURL(),
                                    'inZipPath': TestConfig.getInstance().getSeleniumInZipPath(),
                                    'zipname':   TestConfig.getInstance().getSeleniumZipname(),
                                    'filename':  TestConfig.getInstance().getSeleniumFilename()}
        except KeyError, key:
            print "[ERR] Please specify a value for %s in tests.conf" % key
            sys.exit(1)

        validJars = True

        for name in jarsList:
            jar = jarsList[name]
            #check if jar is already here
            if not os.path.exists(os.path.join(jar['path'], jar['filename'])):
                print "Downloading %s..." % jar['filename']
                try:
                    self.download(jar['url'], jar['path'])

                    #if a zipname is specified, we will unzip the target file pointed by inZipPath variable
                    try:
                        if jar['zipname'] != None:
                            self.unzip(os.path.join(jar['path'], jar['zipname']), jar['inZipPath'], os.path.join(jar['path'], jar['filename']))
                    except KeyError:
                        pass

                except IOError, e:
                    validJars = validJars and False
                    print 'Could not download %s from %s (%s)' % (jar['filename'], jar['url'], e)

        return validJars

    def download(self, url, path):
        """Copy the contents of a file from a given URL
        to a local file.
        """
        import urllib
        webFile = urllib.urlopen(url)
        localFile = open(os.path.join(path, url.split('/')[-1]), 'w')
        localFile.write(webFile.read())
        webFile.close()
        localFile.close()

    def unzip(self, zipPath, inZipPath, targetFile):
        """extract the needed file from zip and then delete the zip"""
        import zipfile
        try:
            zfobj = zipfile.ZipFile(zipPath)
            outfile = open(targetFile, 'wb')
            outfile.write(zfobj.read(inZipPath))
            outfile.flush()
            outfile.close()

            #delete zip file
            os.unlink(zipPath)
        except NameError, e:
            print e

if __name__ == '__main__':
    # Always load source from the current folder
    sys.path = [os.path.abspath('indico')] + sys.path

    #PWD_INDICO_CONF = 'etc/indico.conf'
    #if not os.path.exists(PWD_INDICO_CONF):
    #    shutil.copy('etc/indico.conf.sample', PWD_INDICO_CONF)

    from MaKaC.consoleScripts.installBase import *


    #Dirty trick: For running tests, we need to load all the modules and get rid of unnecessary outputs
    tempLoggingDir = None
    if 'test' in sys.argv:
        import logging
        import tempfile
        tempLoggingDir = tempfile.mkdtemp()
        logging.basicConfig(filename=os.path.join(tempLoggingDir, 'logging'), level=logging.DEBUG)
        setIndicoInstallMode(False)
    else:
        setIndicoInstallMode(True)

    x = vars()
    x.packageDir = os.path.join(get_python_lib(), 'MaKaC')


    x.binDir = 'bin'
    x.documentationDir = 'doc'
    x.configurationDir = 'etc'
    x.htdocsDir = 'htdocs'

    dataFiles = _getDataFiles(x)

    setup(name = "cds-indico",
          cmdclass = {'sdist': sdist_indico,
                    'bdist': _bdist_indico(dataFiles),
                    'bdist_egg': _bdist_egg_indico(dataFiles),
                    'jsbuild': jsbuild,
                    'fetchdeps': fetchdeps_indico,
                    'develop': develop_indico,
                    'test': test_indico,
                    },

          version = _versionInit(),
          description = "Indico is a full-featured conference lifecycle management and meeting/lecture scheduling tool",
          author = "Indico Team",
          author_email = "indico-team@cern.ch",
          url = "http://cdswaredev.cern.ch/indico",
          download_url = "http://cdswaredev.cern.ch/indico/wiki/Releases/Indico0.97.0",
          platforms = ["any"],
          long_description = "Indico allows you to schedule conferences, from single talks to complex meetings with sessions and contributions. It also includes an advanced user delegation mechanism, allows paper reviewing, archival of conference information and electronic proceedings",
          license = "http://www.gnu.org/licenses/gpl-2.0.txt",
          package_dir = { '': 'indico' },
          entry_points = {
            'console_scripts': [ 'taskDaemon           = MaKaC.consoleScripts.taskDaemon:main',
                                 'indico_initial_setup = MaKaC.consoleScripts.indicoInitialSetup:main',
                                 'indico_ctl           = MaKaC.consoleScripts.indicoCtl:main',
                                 ]
          },
          zip_safe = False,
          packages = find_packages(where = 'indico', exclude = ('htdocs',)),
          install_requires = _getInstallRequires(),
          data_files = dataFiles,
          package_data = {'indico': ['*.*'] },
          include_package_data = True,
          dependency_links = [
                              EXTRA_RESOURCES_URL
                              ],
          )

    #delete the temp folder used for logging
    if 'test' in sys.argv:
        shutil.rmtree(tempLoggingDir)
