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
from distutils.sysconfig import get_python_lib, get_python_version
from distutils.cmd import Command
from distutils.command import bdist
from indico.util import i18n


import pkg_resources
from setuptools.command import develop, install, sdist, bdist_egg, easy_install
from setuptools import setup, find_packages, findall


try:
    from babel.messages import frontend as babel
    BABEL_PRESENT = True
except ImportError:
    BABEL_PRESENT = False


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

    base =  ['ZODB3>=3.8', 'pytz', 'zope.index', 'zope.interface',
             'lxml', 'cds-indico-extras', 'zc.queue', 'python-dateutil<2.0',
             'pypdf', 'mako>=0.4.1', 'babel', 'icalendar', 'pyatom', 'python-memcached']

    #for Python older than 2.7
    if sys.version_info[0] <= 2 and sys.version_info[1] < 7:
        base.append('argparse')

    return base


def _versionInit():
        '''Retrieves the version number from indico/MaKaC/__init__.py and returns it'''

        from indico.MaKaC import __version__
        v = __version__

        print('Indico %s' % v)

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
        self.dataFiles += _generateDataPaths([
            ('htdocs/js/presentation/pack', findall('indico/htdocs/js/presentation/pack'), 35),
            ('htdocs/js/indico/pack', findall('indico/htdocs/js/indico/pack'), 29),
            ('htdocs/js/livesync/pack', findall('indico/htdocs/js/indico/pack'), 31),
            ('htdocs/js/jquery/pack', findall('indico/htdocs/js/indico/pack'), 29)])


def _bdist_indico(dataFiles):
    class bdist_indico(bdist.bdist, jsdist_indico):
        def run(self):
            self.jsCompress()
            compileAllLanguages(self)
            bdist.bdist.run(self)

    bdist_indico.dataFiles = dataFiles
    return bdist_indico


def _bdist_egg_indico(dataFiles):
    class bdist_egg_indico(bdist_egg.bdist_egg, jsdist_indico):
        def run(self):
            self.jsCompress()
            compileAllLanguages(self)
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

        wset.resolve(map(pkg_resources.Requirement.parse,
                         filter(lambda x: x != None, _getInstallRequires())),
                     installer=self._installMissing)

        print "Done!"


    def _installMissing(self, dist):
        env = pkg_resources.Environment()
        print dist, EXTRA_RESOURCES_URL
        easy_install.main(["-f", EXTRA_RESOURCES_URL, "-U", str(dist)])
        env.scan()

        if env[str(dist)]:
            return env[str(dist)][0]
        else:
            return None


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

        for f in [x for x in ('etc/zdctl.conf', 'etc/zodb.conf', 'etc/logging.conf') if not os.path.exists(x)]:
            shutil.copy('%s.sample' % f, f)

        print """\nIndico needs to store some information in the filesystem (database, cache, temporary files, logs...)
Please specify the directory where you'd like it to be placed.
(Note that putting it outside of your sourcecode tree is recommended)"""
        prefixDirDefault = os.path.dirname(os.getcwd())
        prefixDir = raw_input('[%s]: ' % prefixDirDefault).strip()

        if prefixDir == '':
            prefixDir = prefixDirDefault

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

        directories.pop('htdocs') #avoid modifying the htdocs folder permissions (it brings problems with git)

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
        compileAllLanguages(self)
        print '''
%s
        ''' % _databaseText('etc')

        if sys.platform == "linux2":
            # create symlink to legacy MaKaC dir
            # this is so that the ".egg-link" created by the "develop" command works
            os.symlink('indico/MaKaC','MaKaC')

    def _update_conf_dir_paths(self, filePath, dirs):
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
                    ('log=', None, "Log to console, using specified level"),
                    ('grid', None, "Use Selenium Grid"),
                    ('xml', None, "XML output"),
                    ('html', None, "Make an HTML report (when possible)"),
                    ('record', None, "Record tests (for --functional)"),
                    ('parallel', None, "Parallel test execution using Selenium Grid (for --functional)"),
                    ('threads=', None, "Parallel test execution with several threads (for --functional)"),
                    ('repeat=', None, "Number of repetitions (for --functional)"),
                    ('silent', None, "Don't output anything in the console, just generate the report")]
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
    silent = False
    html = False
    record = False
    parallel = False
    threads = False
    repeat = False
    log = False
    xml = False

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):

        if not self.checkTestPackages():
            print "Please install those missing packages before launching the tests again"
            sys.exit(-1)

        #missing jars will be downloaded automatically
        if not self.checkTestJars():
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

        if testsToRun == []:
            testsToRun = allTests


        options = {'silent': self.silent,
                   'html': self.html,
                   'specify': self.specify,
                   'coverage': self.coverage,
                   'record': self.record,
                   'parallel': self.parallel,
                   'threads': self.threads,
                   'repeat': self.repeat,
                   'log': self.log,
                   'xml':self.xml}

        # get only options that are active
        options = dict((k,v) for (k,v) in options.iteritems() if v)

        manager = TestManager()

        result = manager.main(testsToRun, options)

        sys.exit(result)

    def checkTestPackages(self):
        packagesList = ['figleaf',
                        'nose',
                        'rednose',
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

    def checkTestJars(self):
        """
        check if needed jars are here, if not,
        dowload them and unzip the file if necessary
        """

        from indico.tests import TestConfig

        jarsList = {}
        currentFilePath = os.path.dirname(__file__)
        testModPath = os.path.join(currentFilePath, 'indico', 'tests')

        try:
            jarsList['jsunit'] = {'path':     os.path.join(testModPath,
                                                           'javascript',
                                                           'unit'),
                                  'url':      TestConfig.getInstance().getJSUnitURL(),
                                  'filename': TestConfig.getInstance().getJSUnitFilename()}

            jarsList['jscoverage'] = {'path':     os.path.join(testModPath,
                                                               'javascript',
                                                               'unit',
                                                               'plugins'),
                                      'url':      TestConfig.getInstance().getJSCoverageURL(),
                                      'filename': TestConfig.getInstance().getJSCoverageFilename()}

            jarsList['selenium'] = {'path':      os.path.join(testModPath,
                                                              'python',
                                                              'functional'),
                                    'url':       TestConfig.getInstance().getSeleniumURL(),
                                    'filename':  TestConfig.getInstance().getSeleniumFilename()}
        except KeyError, key:
            print "[ERR] Please specify a value for %s in tests.conf" % key
            sys.exit(1)

        validJars = True

        for name in jarsList:
            jar = jarsList[name]
            #check if jar is already here
            if not os.path.exists(os.path.join(jar['path'], jar['filename'])):
                print "Downloading %s to %s..." % (jar['url'], jar['path'])
                try:
                    self.download(jar['url'], jar['path'])
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


class egg_filename(Command):
    description = "Get the file name of the generated egg"
    user_options = []
    boolean_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        ei_cmd = self.ei_cmd = self.get_finalized_command("egg_info")
        self.egg_info = ei_cmd.egg_info

        basename = pkg_resources.Distribution(
            None, None, ei_cmd.egg_name, ei_cmd.egg_version,
            get_python_version(),
            self.distribution.has_ext_modules() and pkg_utils.get_build_platform
            ).egg_name()

        print basename


    def run(self):
        pass


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
        logging.basicConfig(filename=os.path.join(tempLoggingDir, 'logging'),
                            level=logging.DEBUG)
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

    foundPackages = find_packages(where = 'indico',
                                  exclude = ('htdocs*', 'tests*', 'core*', 'ext*',
                                             'modules*', 'util*', 'web*', 'locale'))

    # add our namespace package
    foundPackages += list('indico.%s' % pkg for pkg in
                         find_packages(where = 'indico',
                                       exclude = ('htdocs*','MaKaC*')))

    foundPackages.append('indico')

    cmdclass = {'sdist': sdist_indico,
                'bdist': _bdist_indico(dataFiles),
                'bdist_egg': _bdist_egg_indico(dataFiles),
                'jsbuild': jsbuild,
                'fetchdeps': fetchdeps_indico,
                'develop_config': develop_indico,
                'test': test_indico,
                'egg_filename': egg_filename
                }

    if BABEL_PRESENT:
        for cmdname in ['init_catalog', 'extract_messages', 'compile_catalog', 'update_catalog']:
            cmdclass['%s_js' % cmdname] = getattr(babel, cmdname)
        cmdclass['compile_catalog_js'] = i18n.generate_messages_js

    setup(name = "indico",
          cmdclass = cmdclass,
          version = _versionInit(),
          description = "Indico is a full-featured conference lifecycle management and meeting/lecture scheduling tool",
          author = "Indico Team",
          author_email = "indico-team@cern.ch",
          url = "http://cdswaredev.cern.ch/indico",
          download_url = "http://cdswaredev.cern.ch/indico/wiki/Releases/Indico0.97.0",
          platforms = ["any"],
          long_description = "Indico allows you to schedule conferences, from single talks to complex meetings with sessions and contributions. It also includes an advanced user delegation mechanism, allows paper reviewing, archival of conference information and electronic proceedings",
          license = "http://www.gnu.org/licenses/gpl-2.0.txt",
          package_dir = { 'indico': 'indico',
                          'MaKaC' : os.path.join('indico', 'MaKaC')},
          entry_points = """
            [console_scripts]

            indico_scheduler = indico.modules.scheduler.daemon_script:main
            indico_initial_setup = MaKaC.consoleScripts.indicoInitialSetup:main
            indico_ctl = MaKaC.consoleScripts.indicoCtl:main
            indico_livesync = indico.ext.livesync.console:main
            indico_shell = indico.util.shell:main

            [indico.ext_types]

            Collaboration = MaKaC.plugins.Collaboration
            InstantMessaging = MaKaC.plugins.InstantMessaging
            RoomBooking = MaKaC.plugins.RoomBooking
            EPayment = MaKaC.plugins.EPayment
            livesync = indico.ext.livesync
            importer = indico.ext.importer


            [indico.ext]

            Collaboration.EVO = MaKaC.plugins.Collaboration.EVO
            Collaboration.Vidyo = MaKaC.plugins.Collaboration.Vidyo
            Collaboration.CERNMCU = MaKaC.plugins.Collaboration.CERNMCU
            Collaboration.RecordingManager = MaKaC.plugins.Collaboration.RecordingManager
            Collaboration.RecordingRequest = MaKaC.plugins.Collaboration.RecordingRequest
            Collaboration.WebcastRequest = MaKaC.plugins.Collaboration.WebcastRequest

            RoomBooking.CERN = MaKaC.plugins.RoomBooking.CERN
            RoomBooking.default = MaKaC.plugins.RoomBooking.default

            EPayment.payPal = MaKaC.plugins.EPayment.payPal
            EPayment.worldPay = MaKaC.plugins.EPayment.worldPay
            EPayment.yellowPay = MaKaC.plugins.EPayment.yellowPay
            EPayment.skipjack = MaKaC.plugins.EPayment.skipjack

            importer.invenio = indico.ext.importer.invenio
            importer.dummy = indico.ext.importer.dummy

            InstantMessaging.XMPP = MaKaC.plugins.InstantMessaging.XMPP

            livesync.invenio = indico.ext.livesync.invenio
            livesync.cern_search = indico.ext.livesync.cern_search

            """,
          zip_safe = False,
          packages = foundPackages,
          namespace_packages = ['indico'],
          install_requires = _getInstallRequires(),
          data_files = dataFiles,
          package_data = {'indico': ['*.*'] },
          include_package_data = True,
          dependency_links = [
                              EXTRA_RESOURCES_URL
                              ]
          )

    #delete the temp folder used for logging
    if 'test' in sys.argv:
        shutil.rmtree(tempLoggingDir)
