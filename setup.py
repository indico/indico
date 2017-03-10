# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.

# Autoinstalls setuptools if the user doesn't have them already
import ez_setup
ez_setup.use_setuptools()

import commands
import getopt
import os
import getpass
import re
import shutil
import string
import sys
import itertools
from distutils.sysconfig import get_python_lib, get_python_version
from distutils.cmd import Command
from distutils.command import bdist
from indico.util import i18n


import pkg_resources
from setuptools.command import develop, install, sdist, bdist_egg, \
    easy_install, test
from setuptools import setup, find_packages, findall


try:
    from babel.messages import frontend as babel
    BABEL_PRESENT = True
except ImportError:
    BABEL_PRESENT = False

INDICO_PKG_DIR = os.path.join(os.path.dirname(__file__), 'indico')
DEPENDENCY_URLS = ["https://github.com/indico/indico-fonts/releases/"]

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

def read_requirements_file(fname):
    with open(fname, 'r') as f:
        return [dep.strip() for dep in f.readlines() if not (dep.startswith('-') or '://' in dep)]


def _generateDataPaths(x):

    dataFilesDict = {}

    for (baseDstDir, srcDir) in x:
        for f in findall(srcDir):
            dst_dir = os.path.join(baseDstDir,
                                   os.path.relpath(os.path.dirname(f), srcDir))
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
    dataFiles = _generateDataPaths((('bin', 'bin'),
                                    ('doc', 'doc'),
                                    ('etc', 'etc')))
    return dataFiles


def _getInstallRequires():
    '''Returns external packages required by Indico

    These are the ones needed for runtime.'''

    base = read_requirements_file(os.path.join(os.path.dirname(__file__), 'requirements.txt'))

    #for Python older than 2.7
    if sys.version_info[0] <= 2 and sys.version_info[1] < 7:
        base += ['argparse', 'ordereddict']

    return base


def _versionInit():
        '''Retrieves the version number from indico/MaKaC/__init__.py and returns it'''

        from indico.MaKaC import __version__
        v = __version__

        print('Indico %s' % v)

        return v


###  Commands ###########################################################
class sdist_indico(sdist.sdist):
    user_options = (sdist.sdist.user_options +
                    [('version=', None, 'version to distribute')])
    version = 'dev'

    def run(self):
        sdist.sdist.run(self)


def _bdist_indico(dataFiles):
    class bdist_indico(bdist.bdist):
        def run(self):
            compileAllLanguages(self, INDICO_PKG_DIR)
            bdist.bdist.run(self)

    bdist_indico.dataFiles = dataFiles
    return bdist_indico


def _bdist_egg_indico(dataFiles):
    class bdist_egg_indico(bdist_egg.bdist_egg):
        def run(self):
            compileAllLanguages(self, INDICO_PKG_DIR)
            bdist_egg.bdist_egg.run(self)

    bdist_egg_indico.dataFiles = dataFiles
    return bdist_egg_indico


class develop_indico(develop.develop):
    def run(self):
        develop.develop.run(self)

        # create symlink to legacy MaKaC dir
        # this is so that the ".egg-link" created by the "develop" command works
        if sys.platform in ["linux2", "darwin"] and not os.path.exists('MaKaC'):
            os.symlink('indico/MaKaC', 'MaKaC')

        # install dev dependencies
        env = pkg_resources.Environment()
        easy_install.main(read_requirements_file(os.path.join(os.path.dirname(__file__), 'requirements.dev.txt')))
        env.scan()


class develop_config(develop_indico):
    description = "prepares the current directory for Indico development"
    user_options = (develop.develop.user_options +
                    [('www-uid=', None, "Set user for cache/log/db (typically apache user)"),
                     ('www-gid=', None, "Set group for cache/log/db (typically apache group)"),
                     ('http-port=', None, "Set port used by HTTP server"),
                     ('https-port=', None, "Set port used by HTTP server in HTTPS mode"),
                     ('zodb-port=', None, "Set port used by ZODB"),
                     ('smtp-port=', None, "Set port used for SMTP (e-mail sending)"),
                     ('use-apache', None, "Use apache (will chmod directories accordingly)")])

    www_uid = None
    www_gid = None
    http_port = 8000
    https_port = 8443
    zodb_port = 9675
    use_apache = False
    smtp_port = 8025

    def run(self):
        # dependencies, links, etc...
        develop_indico.run(self)

        local = 'etc/indico.conf'
        if os.path.exists(local):
            print 'Upgrading existing etc/indico.conf...'
        else:
            print 'Creating new etc/indico.conf..'
            shutil.copy('etc/indico.conf.sample', local)

        upgrade_indico_conf(local, 'etc/indico.conf.sample', {
                'BaseURL': 'http://localhost:{0}/indico'.format(self.http_port),
                'BaseSecureURL': 'https://localhost:{0}/indico'.format(self.https_port),
                'DBConnectionParams': ("localhost", int(self.zodb_port)),
                'SmtpServer': ("localhost", int(self.smtp_port))
                })

        for f in [x for x in ('etc/zdctl.conf', 'etc/zodb.conf', 'etc/logging.conf') if not os.path.exists(x)]:
            shutil.copy('%s.sample' % f, f)

        print """\nIndico needs to store some information in the filesystem (database, cache, temporary files, logs...)
Please specify the directory where you'd like it to be placed.
(Note that putting it outside of your sourcecode tree is recommended)"""
        prefixDirDefault = os.path.dirname(os.getcwd())
        prefixDir = raw_input('Full path [%s]: ' % prefixDirDefault).strip()

        if prefixDir == '':
            prefixDir = prefixDirDefault

        directories = dict((d, os.path.join(prefixDir, d)) for d in
                           ['db', 'log', 'tmp', 'cache', 'archive'])

        print 'Creating directories...',
        for d in directories.values():
            if not os.path.exists(d):
                os.makedirs(d)
        print 'Done!'

        # add existing dirs
        directories.update(dict((d, os.path.join(os.getcwd(), 'indico', d)) for d in ['htdocs', 'bin', 'etc', 'doc']))

        self._update_conf_dir_paths(local, directories)

        # avoid modifying the htdocs folder permissions (it brings problems with git)
        directories.pop('htdocs')

        from MaKaC.consoleScripts.installBase import _databaseText, _findApacheUserGroup, _checkDirPermissions, \
            _updateDbConfigFiles, _updateMaKaCEggCache

        user = getpass.getuser()
        sourcePath = os.getcwd()

        if self.use_apache:
            # find the apache user/group
            user, group = _findApacheUserGroup(self.www_uid, self.www_gid)
            _checkDirPermissions(directories, dbInstalledBySetupPy=directories['db'], accessuser=user, accessgroup=group)

        _updateDbConfigFiles(os.path.join(sourcePath, 'etc'),
                             db=directories['db'],
                             log=directories['log'],
                             tmp=directories['tmp'],
                             port=self.zodb_port,
                             uid=user)

        _updateMaKaCEggCache(os.path.join(os.path.dirname(__file__), 'indico', 'MaKaC', '__init__.py'),
                             directories['tmp'])

        compileAllLanguages(self, INDICO_PKG_DIR)
        print '''
%s
        ''' % _databaseText('etc')

    def _update_conf_dir_paths(self, filePath, dirs):
        fdata = open(filePath).read()
        for dir in dirs.items():
            d = dir[1].replace("\\", "/")  # For Windows users
            fdata = re.sub('\/opt\/indico\/%s' % dir[0], d, fdata)
        open(filePath, 'w').write(fdata)


class test_indico(test.test):
    """
    Test command for Indico
    """

    description = "Test Suite Framework"
    user_options = (test.test.user_options + [('specify=', None, "Use nosetests style (file.class:testcase)"),
                    ('coverage', None, "Output coverage report in html"),
                    ('unit', None, "Run only Unit tests"),
                    ('functional', None, "Run only Functional tests"),
                    ('pylint', None, "Run python source analysis"),
                    ('jsunit', None, "Run js unit tests"),
                    ('jslint', None, "Run js source analysis"),
                    ('jscoverage', None, "Output coverage report in html for js"),
                    ('jsspecify=', None, "Use js-test-driver style (TestCaseName.testName)"),
                    ('log=', None, "Log to console, using specified level"),
                    ('browser=', None, "Browser to use for functional tests"),
                    ('mode=', None, "Mode to use for functional tests"),
                    ('server-url=', None, "Server URL to use for functional tests"),
                    ('xml', None, "XML output"),
                    ('html', None, "Make an HTML report (when possible)"),
                    ('record', None, "Record tests (for --functional)"),
                    ('silent', None, "Don't output anything in the console, just generate the report"),
                    ('killself', None,
                     "Kill this script right after the tests finished without waiting for db shutdown.")])
    boolean_options = []

    specify = None
    coverage = False
    unit = False
    functional = False
    browser = None
    pylint = False
    jsunit = False
    jslint = False
    jscoverage = False
    jsspecify = None
    silent = False
    mode = None
    server_url = None
    killself = True
    html = False
    record = False
    log = False
    xml = False

    def _wrap(self, func, *params):
        def wrapped():
            self.res = func(*params)
        self.with_project_on_sys_path(wrapped)
        return self.res

    def finalize_options(self):
        testsToRun = []

        allTests = ['unit', 'functional']

        for testType in allTests:
            if getattr(self, testType):
                testsToRun.append(testType)

        if self.jsspecify and 'jsunit' not in testsToRun:
            testsToRun.append('jsunit')

        if testsToRun == []:
            testsToRun = allTests
        self.testsToRun = testsToRun

    def run(self):

        if self.distribution.install_requires:
            self.distribution.fetch_build_eggs(self.distribution.install_requires)
        if self.distribution.tests_require:
            self.distribution.fetch_build_eggs(self.distribution.tests_require)

        from indico.tests import TestManager

        options = {'silent': self.silent,
                   'killself': self.killself,
                   'html': self.html,
                   'browser': self.browser,
                   'mode': self.mode,
                   'specify': self.specify,
                   'coverage': self.coverage,
                   'record': self.record,
                   'server_url': self.server_url,
                   'log': self.log,
                   'xml': self.xml}

        # get only options that are active
        options = dict((k, v) for (k, v) in options.iteritems() if v)

        manager = TestManager()
        result = self._wrap(manager.main, self.testsToRun, options)

        sys.exit(result)

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
            self.distribution.has_ext_modules() and pkg_utils.get_build_platform).egg_name()

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

    foundPackages = list('MaKaC.%s' % pkg for pkg in
                         find_packages(where='indico/MaKaC'))
    foundPackages.append('MaKaC')
    foundPackages.append('htdocs')

    # add our namespace package
    foundPackages += list('indico.%s' % pkg for pkg in
                          find_packages(where='indico',
                                        exclude=['htdocs*', 'MaKaC*']))
    foundPackages.append('indico')

    cmdclass = {'sdist': sdist_indico,
                'bdist': _bdist_indico(dataFiles),
                'bdist_egg': _bdist_egg_indico(dataFiles),
                'develop_config': develop_config,
                'develop': develop_indico,
                'test': test_indico,
                'egg_filename': egg_filename
                }

    if BABEL_PRESENT:
        for cmdname in ['init_catalog', 'extract_messages', 'compile_catalog', 'update_catalog']:
            cmdclass['%s_js' % cmdname] = getattr(babel, cmdname)
        cmdclass['compile_catalog_js'] = i18n.generate_messages_js

    setup(name="indico",
          cmdclass=cmdclass,
          version=_versionInit(),
          description="Indico is a full-featured conference lifecycle management and meeting/lecture scheduling tool",
          author="Indico Team",
          author_email="indico-team@cern.ch",
          url="http://indico-software.org",
          download_url="https://github.com/indico/indico/releases/tag/v1.2.2rc1",
          platforms=["any"],
          long_description="Indico allows you to schedule conferences, from single talks to complex meetings with "
                           "sessions and contributions. It also includes an advanced user delegation mechanism, "
                           "allows paper reviewing, archival of conference information and electronic proceedings",
          license="http://www.gnu.org/licenses/gpl-3.0.txt",
          entry_points="""
            [console_scripts]

            indico_scheduler = indico.modules.scheduler.daemon_script:main
            indico_initial_setup = MaKaC.consoleScripts.indicoInitialSetup:main
            indico_ctl = MaKaC.consoleScripts.indicoCtl:main
            indico_livesync = indico.ext.livesync.console:main
            indico_shell = indico.util.shell:main
            indico_admin = indico.util.admin:main

            [indico.ext_types]

            statistics = indico.ext.statistics
            Collaboration = MaKaC.plugins.Collaboration
            InstantMessaging = MaKaC.plugins.InstantMessaging
            RoomBooking = MaKaC.plugins.RoomBooking
            EPayment = MaKaC.plugins.EPayment
            livesync = indico.ext.livesync
            importer = indico.ext.importer
            calendaring = indico.ext.calendaring
            search = indico.ext.search

            [indico.ext]

            statistics.piwik = indico.ext.statistics.piwik

            Collaboration.EVO = MaKaC.plugins.Collaboration.EVO
            Collaboration.WebEx = MaKaC.plugins.Collaboration.WebEx
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

            calendaring.outlook = indico.ext.calendaring.outlook

            search.invenio = indico.ext.search.invenio

            """,
          zip_safe=False,
          packages=foundPackages,
          package_dir={'indico': 'indico',
                       'htdocs': os.path.join('indico', 'htdocs'),
                       'MaKaC': os.path.join('indico', 'MaKaC')},
          package_data={'indico': ['*.*']},
          include_package_data=True,
          namespace_packages=['indico', 'indico.ext'],
          install_requires=_getInstallRequires(),
          tests_require=['nose', 'rednose', 'twill', 'selenium', 'figleaf'],
          data_files=dataFiles,
          dependency_links=DEPENDENCY_URLS
          )

    #delete the temp folder used for logging
    if 'test' in sys.argv:
        shutil.rmtree(tempLoggingDir)
