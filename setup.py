# -*- coding: utf-8 -*-
##
## $Id: setup.py,v 1.122 2009/06/17 15:27:43 jose Exp $
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

from setuptools.command import develop, install, sdist
from setuptools import setup, find_packages, findall
from subprocess import Popen, PIPE

if sys.platform == 'linux2':
    import pwd
    import grp

import tests

INDICO_INSTALL = True # Needed by common/__init__.py

if os.path.exists('etc/indico.conf.local'):
    PWD_INDICO_CONF = 'etc/indico.conf.local'
else:
    PWD_INDICO_CONF = 'etc/indico.conf'
    
class Vars:
    '''Variable holder.'''
    packageDir = None
    localDatabaseDir = '/opt/indico/db'
    versionVal = 'None'
    accessuser = None
    accessgroup = None
    dbInstalledBySetupPy = False


def getDataFiles(x):
    '''Returns a fully populated data_files ready to be fed to setup()'''
    cfg = Config.getInstance()
    dataFilesDict = {}

    # setup expects a list like this (('foo/bar/baz', 'wiki.py'),
    #                                 ('a/b/c', 'd.jpg'))
    #
    # What we do below is transform a list like this:
    #                                (('foo', 'bar/baz/wiki.py'),
    #                                 ('a', 'b/c/d.jpg'))
    #
    # first into a dict and then into a pallatable form for setuptools.
    
    for (baseDstDir, files, remove_first_x_chars) in ((cfg.getBinDir(),           findall('bin'), 4),
                                                      (cfg.getDocumentationDir(), ['doc/UserGuide.pdf','doc/AdminUserGuide.pdf'], 4),
                                                      (cfg.getConfigurationDir(), findall('etc'), 4),
                                                      (x.packageDir,              findall('indico/MaKaC'), 13),
                                                      (cfg.getHtdocsDir(),        findall('indico/htdocs'), 14),
                                                      ):
        for f in files:
            dst_dir = os.path.join(baseDstDir, os.path.dirname(f)[remove_first_x_chars:])
            if dst_dir not in dataFilesDict:
                dataFilesDict[dst_dir] = []
            dataFilesDict[dst_dir].append(f)

    dataFiles = []
    for k, v in dataFilesDict.items():
        dataFiles.append((k, v))

    return dataFiles


def upgrade_indico_conf(existing_conf, new_conf, mixinValues={}):
    '''Copies new_conf values to existing_conf preserving existing_conf's values
    
    If mixinValues is given its items will be preserved above existing_conf's values and new_conf's values'''
    
    # We retrieve values from newest indico.conf
    execfile(new_conf)
    new_values = locals()
    # We retrieve values from existing indico.conf
    execfile(existing_conf)
    existing_values = locals()
   
    new_values.update(existing_values)
    new_values.update(mixinValues)
    
    # We have to preserve options not currently present in the bundled indico.conf because they
    # may belong to a plugin. This functionality can lead to forget adding new options to
    # Configuration.py so be careful my friend. 
    
    # We remove vars defined here that aren't options
    for k in ('new_values', 'new_conf', 'existing_conf', 'mixinValues'):
        new_values.pop(k)
        
    result_values = new_values

    # We update a current copy of indico.conf with the new values
    new_contents = open(new_conf).read()
    for k in new_values:
        if new_values[k].__class__ == str:
            regexp = re.compile('^(%s[ ]*=[ ]*[\'"]{1})([^\'"]*)([\'"]{1})' % k, re.MULTILINE)
            if regexp.search(new_contents):
                new_contents = re.sub(regexp, "\\g<1>%s\\3" % result_values[k], new_contents)
            else:
                new_contents = "%s\n%s = '%s'" % (new_contents, k, result_values[k])
        elif new_values[k].__class__ == int:
            regexp = re.compile('^(%s[ ]*=[ ]*)([0-9]+)' % k, re.MULTILINE)
            if regexp.search(new_contents):
                new_contents = re.sub(regexp, "\\g<1>%s" % result_values[k], new_contents)
            else:
                new_contents = "%s\n%s = %s" % (new_contents, k, str(result_values[k]))
            
        elif new_values[k].__class__ == tuple:
            regexp = re.compile('^(%s[ ]*=[ ]*)[\(]{1}([^\)]+)[\)]{1}' % k, re.MULTILINE)
            if regexp.search(new_contents):
                new_contents = re.sub(regexp, "\\g<1>%s" % str(result_values[k]), new_contents)
            else:
                new_contents = "%s\n%s = %s" % (new_contents, k, str(result_values[k]))
            
        elif new_values[k].__class__ == dict:
            regexp = re.compile('^(%s[ ]*=[ ]*)[\{]{1}([^\}]+)[\}]{1}' % k, re.MULTILINE)
            if regexp.search(new_contents):
                new_contents = re.sub(regexp, "\\g<1>%s" % str(result_values[k]), new_contents)
            else:
                new_contents = "%s\n%s = %s" % (new_contents, k, str(result_values[k]))
            
        elif new_values[k].__class__ == list:
            regexp = re.compile('^(%s[ ]*=[ ]*)[\[]{1}([^\]]+)[\]]{1}' % k, re.MULTILINE)
            if regexp.search(new_contents):
                new_contents = re.sub(regexp, "\\g<1>%s" % str(result_values[k]), new_contents)
            else:
                new_contents = "%s\n%s = %s" % (new_contents, k, str(result_values[k]))
        else:
            raise 'Invalid config value "%s = %s"' % (k, new_values[k])
    
    # We write unknown options to the end of the file, they may not be just outdated options but plugins' 
    open(existing_conf, 'w').write(new_contents)


def modifyOnDiskIndicoConfOption(indico_conf, optionName, optionValue):
    upgrade_indico_conf(indico_conf, indico_conf, {optionName: optionValue})
        

def updateIndicoConfPathInsideMaKaCConfig(indico_conf_path, makacconfigpy_path):
        '''Modifies the location of indico.conf referenced inside makacconfigpy_path to
        point to indico_conf_path'''
        fdata = open(makacconfigpy_path).read()
        fdata = re.sub('indico_conf[ ]*=[ ]*[\'"]{1}([^\'"]*)[\'"]{1}', "indico_conf = \"%s\"" % indico_conf_path, fdata)
        open(makacconfigpy_path, 'w').write(fdata)


def confmerge(oldDict, newDict):
    '''Merges an existing configuration (dict) with a new configuration (dict).

       Rules:
        if existing config has a key that does not appear in the new config it will not be copied to the final config
        if existing config has a key with a None or '' value then it will take whatever value that option has in the new config
        if a value is a list then items existing in the oldconfig will be preserved and new items present in the newconfig will be appended
    '''
    resultDict = newDict

    for k, v in newDict.items():
        if k in oldDict.keys():
            oldVal = oldDict[k]
            if v.__class__.__name__ == 'tuple':
                # the dict.fromkeys just returns a list without duplicated values.
                # It is O(n): http://mail.python.org/pipermail/python-list/2004-January/244374.html
                resultDict[k] = oldVal
            elif v.__class__.__name__ == 'list':
                resultDict[k] = dict.fromkeys(v + oldVal).keys()
            elif oldVal != None and oldVal != '':
                resultDict[k] = oldVal

    return resultDict


def compileAllLanguages():
    '''Generates .mo files from .po files'''
    pwd = os.getcwd()
    os.chdir('./indico/MaKaC/po')
    os.system('%s compile-all-lang.py --quiet' % sys.executable)
    os.chdir(pwd)


def jsCompress():
    '''Packs and minifies javascript files'''
    jsbuildPath = 'jsbuild'
    os.chdir('./etc/js')
    os.system('%s -o ../../indico/htdocs/js/indico/pack indico.cfg' % jsbuildPath)
    os.system('%s -o ../../indico/htdocs/js/presentation/pack presentation.cfg' % jsbuildPath )
    os.chdir('../..')


def getInstallRequires():
    base =  ['pytz', 'zodb3', 'jstools', 'zope.index', 'simplejson', 'lxml', 'ReportLab']
    if sys.version_info[1] < 5: # hashlib is part of Python 2.5+
        base.append('hashlib')
    return base


def versionInit():
        '''Writes the version number inside indico/MaKaC/__init__.py'''
        global x
        v = None
        try:
            opts, args = getopt.gnu_getopt(sys.argv[1:], "", ["version="])

            for o, a in opts:
                if o == '--version':
                    v = a
                    break
        except getopt.GetoptError:
            v = 'dev'

        if not v:
            v = raw_input('Version being packaged [dev]: ').strip()
            if v == '':
                v = 'dev'

        old_init = open('indico/MaKaC/__init__.py','r').read()
        new_init = re.sub('(__version__[ ]*=[ ]*[\'"]{1})([^\'"]+)([\'"]{1})', "\\g<1>%s\\3" % v, old_init)
        open('indico/MaKaC/__init__.py', 'w').write(new_init)
        return v


def checkModPythonIsInstalled():
    try:
        import mod_python
    except ImportError:
        raw_input('''
WARNING: mod_python is not installed. You need to install Apache and mod_python
         before you can run Indico.

You can download Apache from:

    http://httpd.apache.org/


You can downlod mod_python from:

    http://www.modpython.org/

Press any key to continue...''')

###  Commands ###########################################################
class sdist_indico(sdist.sdist):
    user_options = sdist.sdist.user_options + \
                   [('version=', None, 'version to distribute')]
    version = 'dev'

    def run(self):
        global x

        self._convertdoc()
        jsCompress()
        sdist.sdist.run(self)


    def _convertdoc(self):
        '''Generates INSTALL from INSTALL.xml'''
        commands.getoutput('docbook2html --nochunks doc/docbook_src/INSTALL.xml > INSTALL.html')
        commands.getoutput('docbook2pdf doc/docbook_src/INSTALL.xml')
        commands.getoutput('w3m INSTALL.html > INSTALL')
        commands.getoutput('rm INSTALL.html')


class install_indico(install.install):
    user_options = [('uid=', None, "uid of Apache user\n\n"),
                    ('gid=', None, 'gid of Apache user'),
                    ('config-dir=', None, 'directory to store indico.conf'),
                    ('force-upgrade', None, 'upgrade without asking for confirmation first')] + install.install.user_options

    uid = None
    gid = None
    config_dir = None
    force_upgrade = False

    def run(self):
        cfg = Config.getInstance()

        if self.root != None and sys.path[0] != os.path.join(self.root, 'MaKaC'):
            sys.path = [os.path.join(self.root, 'MaKaC')] + sys.path

        self._resolvePackageDir()

        if self.config_dir == None:
            self.config_dir = cfg.getConfigurationDir()
        
        self._makaccconfig_base_dir = '%s/MaKaC/common' % self.install_lib
        
        if self._existingInstallation():
            if self.force_upgrade:
                print 'Upgrading existing Indico installation..'
            else:
                opt = None

                while opt not in ('', 'e', 'E', 'u'):
                    opt = raw_input('''
An existing Indico installation has been detected at:

    %s

At this point you can:

    [u]pgrade the existing installation

    [E]xit this installation process

What do you want to do [u/E]? ''' % self._existingIndicoConfPath())
                if opt in ('', 'e', 'E'):
                    print "\nExiting installation..\n"
                    sys.exit()
                elif opt == 'u':
                    self._activateIndicoConfFromExistingInstallation()


        compileAllLanguages()
        indicoconfpath = os.path.join(self.config_dir, 'indico.conf')
          
        updateIndicoConfPathInsideMaKaCConfig(indicoconfpath, os.path.join('indico', 'MaKaC', 'common', 'MaKaCConfig.py'))
        install.install.run(self)
        self._createDirs(x)
        
        updateIndicoConfPathInsideMaKaCConfig(indicoconfpath, os.path.join(self._makaccconfig_base_dir, 'MaKaCConfig.py'))

        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

        for f in [xx for xx in ('%s/zdctl.conf' % self.config_dir, '%s/zodb.conf' % self.config_dir) if not os.path.exists(xx)]:
            shutil.copy('%s.sample' % f, f)

        if not os.path.exists(indicoconfpath):
            shutil.copy(PWD_INDICO_CONF, indicoconfpath)

        upgrade_indico_conf(indicoconfpath, PWD_INDICO_CONF)
            
        
        if not self._existingDb():
            opt = None
            while opt not in ('Y', 'y', 'n', ''):
                opt = raw_input('''\nWe cannot connect to the configured database at %s.

Do you want to create a new database now [Y/n]? ''' % str(cfg.getDBConnectionParams()))
                if opt in ('Y', 'y', ''):
                    x.dbInstalledBySetupPy = True
                    dbpath_ok = False
                    while not dbpath_ok:
                        dbpath = raw_input('''\nWhere do you want to install the database [/opt/indico/db]? ''')
                        if dbpath.strip() == '':
                            dbpath = '/opt/indico/db'

                        try:
                            os.makedirs(dbpath)
                            dbpath_ok = True
                        except Exception:
                            print 'Unable to create database at %s, please make sure that you have permissions to create that directory' % dbpath

                elif opt == 'n':
                    sys.exit()

        self._checkDirPermissions(x)

        checkModPythonIsInstalled()

        print """

Congratulations!
Indico has been installed correctly.

    indico.conf:      %s/indico.conf

    BinDir:           %s
    DocumentationDir: %s
    ConfigurationDir: %s
    PackageDir:       %s
    HtdocsDir:        %s


Please do not forget to start the 'taskDaemon' in order to use alarms, creation
of off-line websites, reminders, etc. You can find it in './bin/taskDaemon.py'

Add the following lines to your Apache2 httpd.conf:

<Directory "%s">
    AddHandler python-program .py
    PythonHandler mod_python.publisher
    PythonDebug On
    PythonPath "sys.path + ['%s']"
</Directory>

<Directory "%s/services">
    SetHandler python-program
    PythonHandler MaKaC.services.handler
    PythonInterpreter main_interpreter
    Allow from All
</Directory>



If you are running ZODB on this host:
- Review %s/zodb.conf and %s/zdctl.conf to make sure everything is ok.
- To start the database run: zdctl.py -C %s/zdctl.conf start
""" % (cfg.getConfigurationDir(), cfg.getBinDir(), cfg.getDocumentationDir(), cfg.getConfigurationDir(), x.packageDir, cfg.getHtdocsDir(), cfg.getHtdocsDir(), x.packageDir, cfg.getHtdocsDir(),  cfg.getConfigurationDir(), cfg.getConfigurationDir(), cfg.getConfigurationDir())


    def _existingDb(self):
        return os.path.exists(x.localDatabaseDir)


    def _activateIndicoConfFromExistingInstallation(self):
        '''Updates the MaKaCConfig file inside the directory from which we
        are installing and forces Configuration to reload its values
        '''

        updateIndicoConfPathInsideMaKaCConfig(self._existingIndicoConfPath(),
                                              os.path.join('indico', 'MaKaC', 'common', 'MaKaCConfig.py'))

        Config.getInstance().forceReload()
        self.data_files = getDataFiles(x)


    def _existingInstallation(self):
        '''Returns true if an existing installation has been detected.

           We consider that an existing installation exists if there is an
           "indico.conf" file inside the directory pointed by the
           ConfigurationDir var of the "indico.conf from this directory.'''
        return os.path.exists(self._existingIndicoConfPath())


    def _existingIndicoConfPath(self):
        cfg = Config.getInstance()

        return os.path.join(cfg.getConfigurationDir(), 'indico.conf')


    def _resolvePackageDir(self):
        # TODO DEPRECATED, USAR PARAM DE SETUPTOOLS
        x.packageDir = get_python_lib()
        if self.root:
            x.packageDir = x.packageDir[1:]

        self.install_purelib = x.packageDir


    def _createDirs(self, x):
        cfg = Config.getInstance()
        for dir in (cfg.getLogDir(), cfg.getUploadedFilesTempDir()):
            if not os.path.exists(dir):
                os.makedirs(dir)


    def _checkDirPermissions(self, x):
        cfg = Config.getInstance()

        # if we are on linux we need to give proper permissions to the results directory
        if sys.platform == "linux2":
            prompt = True

            # Check to see if uid/gid were provided through commandline
            if self.uid and self.gid:
                try:
                    pwd.getpwuid(int(self.uid))
                    grp.getgrgid(int(self.gid))
                    x.accessuser = int(self.uid)
                    x.accessgroup = int(self.gid)
                    prompt = False
                except KeyError:
                    print 'Invalid pair uid/gid (%s/%s)' % (self.uid, self.gid)

            # Try to use indico.conf's
            try:
                pwd.getpwnam(cfg.getApacheUser())
                grp.getgrnam(cfg.getApacheGroup())
                x.accessuser = cfg.getApacheUser()
                x.accessgroup = cfg.getApacheGroup()
                prompt = False
            except KeyError:
                print "\nERROR: indico.conf's ApacheUser and ApacheGroup options are incorrect (%s/%s)." % (cfg.getApacheUser(), cfg.getApacheGroup())

            if prompt == True:
                valid_credentials = False
                while not valid_credentials:
                    x.accessuser = raw_input("\nPlease enter the user that will be running the Apache server: ")
                    x.accessgroup = raw_input("\nPlease enter the group that will be running the Apache server: ")
                    try:
                        pwd.getpwnam(x.accessuser)
                        grp.getgrnam(x.accessgroup)
                        valid_credentials = True
                    except KeyError:
                        print "\nERROR: Invalid user/group pair (%s/%s)" % (x.accessuser, x.accessgroup)
                    
                    modifyOnDiskIndicoConfOption(PWD_INDICO_CONF, 'ApacheUser', x.accessuser)
                    modifyOnDiskIndicoConfOption(PWD_INDICO_CONF, 'ApacheGroup', x.accessgroup)

            dirs2check = [cfg.getPublicFolder(), cfg.getLogDir(), cfg.getUploadedFilesTempDir()]
            if x.dbInstalledBySetupPy:
                dirs2check.append(x.localDatabaseDir)

            for dir in dirs2check:
                commands.getoutput("chown -r %s:%s %s" % (x.accessuser, x.accessgroup, dir))


class jsbuild(Command):
    description = "minifies and packs javascript files"
    user_options = []
    boolean_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        jsCompress()


class develop_indico(Command):
    description = "prepares the current directory for Indico development"
    user_options = []
    boolean_options = []

    def initialize_options(self): pass

    def finalize_options(self): pass

    def run(self):
        local = 'etc/indico.conf.local'
        if os.path.exists(local):
            print 'Upgrading existing etc/indico.conf.local..'
            upgrade_indico_conf(local, 'etc/indico.conf')
        else:
            print 'Creating new etc/indico.conf.local..'
            shutil.copy('etc/indico.conf', local)

        for d in [x for x in ('db', 'log') if not os.path.exists(x)]:
            os.makedirs(d)

        for f in [x for x in ('etc/zdctl.conf', 'etc/zodb.conf') if not os.path.exists(x)]:
            shutil.copy('%s.sample' % f, f)

        updateIndicoConfPathInsideMaKaCConfig(os.path.join(os.path.dirname(__file__), ''), 'indico/MaKaC/common/MaKaCConfig.py')
        compileAllLanguages()
        print '''
IMPORTANT NOTES

- Review etc/indico.conf.local, etc/zodb.conf and etc/zdctl.conf to make sure everything is ok.

- To start the database run: zdctl.py -C etc/zdctl.conf start
'''


class tests_indico(Command):
    description = "run the test suite"
    user_options = []
    boolean_options = []

    def initialize_options(self): pass

    def finalize_options(self): pass

    def run(self):
        p = Popen("%s tests/__init__.py" % sys.executable, shell=True, stdout=PIPE, stderr=PIPE)
        out = string.join(p.stdout.readlines() )
        outerr = string.join(p.stderr.readlines() )
        print out, outerr


if __name__ == '__main__':
    INDICO_INSTALL = True
    sys.path = ['indico'] + sys.path

    try:
        from MaKaC.common.Configuration import Config
    except IOError:
        # If an installation is halfway aborted we can end up with a broken MaKaCConfig in the installation dir
        updateIndicoConfPathInsideMaKaCConfig(PWD_INDICO_CONF, os.path.join('indico', 'MaKaC', 'common', 'MaKaCConfig.py'))
        from MaKaC.common.Configuration import Config

    from MaKaC.i18n import _

    x = Vars()
    x.packageDir = os.path.join(get_python_lib(), 'MaKaC')

    if 'sdist' in sys.argv or 'bdist_egg' in sys.argv: # we need to calculate version at this point, before sdist_indico runs
        x.versionVal = versionInit()

    setup(name = "cds-indico",
          cmdclass={'sdist': sdist_indico,
                    'jsbuild': jsbuild,
                    'install': install_indico,
                    'tests': tests_indico,
                    'develop': develop_indico,
                    },

          version = x.versionVal,
          description = "Integrated Digital Conferences",
          author = "AVC Section@CERN-IT",
          author_email = "indico-project@cern.ch",
          url = "http://cern.ch/indico",
          download_url = "http://cern.ch/indico/download.html",
          platforms = ["any"],
          long_description = "Integrated Digital Conferences",
          license = "http://www.gnu.org/licenses/gpl-2.0.txt",
          package_dir = { '': 'indico' },
          packages = find_packages(where='indico', exclude=('htdocs',)),
          install_requires = getInstallRequires(),
          data_files = getDataFiles(x),
          package_data = {'indico': ['*.*'] },
          include_package_data = True,
          )
