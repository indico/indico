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

from setuptools.command import develop, install, sdist
from setuptools import setup, find_packages, findall
from subprocess import Popen, PIPE

if sys.platform == 'linux2':
    import pwd
    import grp

import tests

    
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
def _getDataFiles(x):
    '''Returns a fully populated data_files ready to be fed to setup()
    
    WARNING: when creating a bdist_egg we need to include files inside bin, 
    doc, config & htdocs into the egg therefore we cannot fetch indico.conf 
    values directly because they will not refer to the proper place. We 
    include those files in the egg's root folder. 
    '''
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

    # This re will be used to filter out etc/*.conf files and therefore not overwritting them
    isAConfRe = re.compile('etc\/[^/]+\.conf$')
    
    for (baseDstDir, files, remove_first_x_chars) in ((x.binDir,           findall('bin'), 4),
                                                      (x.documentationDir, ['doc/UserGuide.pdf','doc/AdminUserGuide.pdf'], 4),
                                                      (x.configurationDir, [xx for xx in findall('etc') if not isAConfRe.search(xx)], 4),
                                                      (x.packageDir,              findall('indico/MaKaC'), 13),
                                                      (x.htdocsDir,        findall('indico/htdocs'), 14),
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





def _getInstallRequires():
    '''Returns external packages required by Indico
    
    They will only be installed when Indico is installed through easy_install.'''
    
    base =  ['pytz', 'zodb3', 'jstools', 'zope.index', 'simplejson']
    if sys.version_info[1] < 5: # hashlib is part of Python 2.5+
        base.append('hashlib')
        
    return base


def _versionInit():
        '''Writes a version number inside indico/MaKaC/__init__.py and returns it'''
        global x
        v = None
        for k in sys.argv:
            if k == '--version':
                v = sys.argv[sys.argv.index(k) + 1]
                break

        if not v:
            v = raw_input('Version being packaged [dev]: ').strip()
            if v == '':
                v = 'dev'

        old_init = open('indico/MaKaC/__init__.py','r').read()
        new_init = re.sub('(__version__[ ]*=[ ]*[\'"]{1})([^\'"]+)([\'"]{1})', "\\g<1>%s\\3" % v, old_init)
        open('indico/MaKaC/__init__.py', 'w').write(new_init)
        return v


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
                    ('force-no-db', None, 'force not to detect if DB installed'),
                    ('force-upgrade', None, 'upgrade without asking for confirmation first')] + install.install.user_options

    uid = None
    gid = None
    config_dir = None
    force_no_db = False
    force_upgrade = False

    def run(self):
        if self.root != None and sys.path[0] != os.path.join(self.root, 'MaKaC'):
            sys.path = [os.path.join(self.root, 'MaKaC')] + sys.path
        
        # If we don't do the following then BinDir, ConfigurationDir, etc will have 
        # self.install_data preppended to them therefore ignoring absolute paths specified in
        # indico.conf.
        self.install_data = ''
        
        self._resolvePackageDir()
        
        # Indico can be installed both through setup.py and easy_install. To support the latter
        # we need to split installation steps in external functions that can also be called
        # by indico_initial_setup.
        cfg = Config.getInstance()
        if self.config_dir == None:
            self.config_dir = cfg.getConfigurationDir()
            
        indico_pre_install(self.config_dir, force_upgrade=self.force_upgrade)
        
        install.install.run(self) # this basically copies files to site-packages (or dist-packages)
        
        makacconfig_base_dir = '%s/MaKaC/common' % self.install_lib
        indico_post_install(self.config_dir,
                            makacconfig_base_dir,
                            self._resolvePackageDir(),
                            self.force_no_db,
                            self.uid,
                            self.gid)
    

    def _resolvePackageDir(self):
        '''Returns the path where the pure Python package (MaKaC) will be installed to
        
        We need to touch it primarily because of the tests where we are specifying a root 
        folder.'''
        x.packageDir = get_python_lib()
        if self.root:
            x.packageDir = x.packageDir[1:]

        self.install_purelib = x.packageDir



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


class develop_indico(Command):
    description = "prepares the current directory for Indico development"
    user_options = []
    boolean_options = []

    def initialize_options(self): pass

    def finalize_options(self): pass

    def run(self):
        local = 'etc/indico.conf'
        if os.path.exists(local):
            print 'Upgrading existing etc/indico.conf..'
            upgrade_indico_conf(local, 'etc/indico.conf.sample')
        else:
            print 'Creating new etc/indico.conf..'
            shutil.copy('etc/indico.conf.sample', local)

        for d in [x for x in ('db', 'log') if not os.path.exists(x)]:
            os.makedirs(d)

        for f in [x for x in ('etc/zdctl.conf', 'etc/zodb.conf') if not os.path.exists(x)]:
            shutil.copy('%s.sample' % f, f)
        createDirs()
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
    sys.path = ['indico'] + sys.path # Always load source from the current folder
    
    #PWD_INDICO_CONF = 'etc/indico.conf'
    #if not os.path.exists(PWD_INDICO_CONF):
    #    shutil.copy('etc/indico.conf.sample', PWD_INDICO_CONF)
    
    from MaKaC.consoleScripts.installBase import *
    setIndicoInstallMode(True)

    try:
        from MaKaC.common.Configuration import Config
    except IOError:
        # If an installation is halfway aborted we can end up with a
        # broken indico_conf value inside MaKaCConfig from the installation dir.
        updateIndicoConfPathInsideMaKaCConfig('etc/indico.conf.sample', os.path.join('indico', 'MaKaC', 'common', 'MaKaCConfig.py'))
        from MaKaC.common.Configuration import Config
    
    
    x = vars()
    x.packageDir = os.path.join(get_python_lib(), 'MaKaC')

    # we need to calculate version at this point, before sdist_indico runs
    if 'sdist' in sys.argv or 'bdist_egg' in sys.argv: 
        x.versionVal = _versionInit()
        
        
    if 'bdist_egg' in sys.argv:
        x.binDir = 'bin'
        x.documentationDir = 'doc'
        x.configurationDir = 'etc'
        x.htdocsDir = 'htdocs'
    else:
        cfg = Config.getInstance()
        x.binDir = cfg.getBinDir()
        x.documentationDir = cfg.getDocumentationDir()
        x.configurationDir = cfg.getConfigurationDir()
        x.htdocsDir = cfg.getHtdocsDir()  


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
          download_url = "http://cern.ch/indico/download-beta.html",
          platforms = ["any"],
          long_description = "Integrated Digital Conferences",
          license = "http://www.gnu.org/licenses/gpl-2.0.txt",
          package_dir = { '': 'indico' },
          entry_points = {
            'console_scripts': [ 'taskDaemon           = MaKaC.consoleScripts.taskDaemon:main',
                                 'indico_initial_setup = MaKaC.consoleScripts.indicoInitialSetup:main',
                                 'indico_ctl           = MaKaC.consoleScripts.indicoCtl:main',
                                 ]
          },
          zip_safe = False,
          packages = find_packages(where='indico', exclude=('htdocs',)),
          install_requires = _getInstallRequires(),
          data_files = _getDataFiles(x),
          package_data = {'indico': ['*.*'] },
          include_package_data = True,
          )
