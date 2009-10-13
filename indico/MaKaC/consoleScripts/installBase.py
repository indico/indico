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

'''This file contains functions used by both 'python setup.py install' and after-easy_install
based installations.
''' 

import commands
import getopt
import os
import re
import shutil
import string
import sys

if sys.platform == 'linux2':
    import pwd
    import grp

import MaKaC

INDICO_INSTALL = False

LOCALDATABASEDIR = '/opt/indico/db'
PWD_INDICO_CONF = 'etc/indico.conf'


def setIndicoInstallMode(newmode):
    '''Sets indico install mode. 
    
    This function and getIndicoInstallMode are used by some __init__.py inside 
    MaKaC to load or not some modules. At installation time those modules are not 
    available. That's why we need to skip them. They are imported there only as
    shortcuts.'''  
    global INDICO_INSTALL
    INDICO_INSTALL = newmode


def getIndicoInstallMode():
    global INDICO_INSTALL
    return INDICO_INSTALL
    
    
def createDirs():
    '''Creates directories that are not automatically created by setup.install or easy_install'''
    from MaKaC.common.Configuration import Config
    cfg = Config.getInstance()
    
    for dir in (cfg.getLogDir(), 
                cfg.getUploadedFilesTempDir(), 
                cfg.getXMLCacheDir()):
        if not os.path.exists(dir):
            os.makedirs(dir)
         
             
def upgrade_indico_conf(existing_conf, new_conf, mixinValues={}):
    '''Copies new_conf values to existing_conf file preserving existing_conf's values
    
    If mixinValues is given its items will be preserved above existing_conf's values and new_conf's values'''
    
    # We retrieve values from newest indico.conf
    execfile(new_conf)
    new_values = locals().copy()
    # We retrieve values from existing indico.conf
    execfile(existing_conf)
    existing_values = locals().copy()

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


def compileAllLanguages():
    '''Generates .mo files from .po files'''
    pwd = os.getcwd()
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(MaKaC.__file__)), 'po'))
    os.system('%s compile-all-lang.py --quiet' % sys.executable)
    os.chdir(pwd)

        
def copytreeSilently(source, target):
    '''Copies source tree to target tree overwriting existing files'''
    source = os.path.normpath(SOURCE)
    target = os.path.normpath(TARGET)
    for root, dirs, files in os.walk(source, topdown=False):
        for name in files:
            fullpath = os.path.normpath(os.path.join(root, name))
            dstfile = os.path.normpath(fullpath.replace(source, target))
            targetdir = os.path.dirname(dstfile)
            if not os.path.exists(targetdir):
                os.makedirs(targetdir)
            try:
                shutil.copy(fullpath, dstfile)
            except Exception, e:
                print e


def jsCompress():
    '''Packs and minifies javascript files'''
    jsbuildPath = 'jsbuild'
    os.chdir('./etc/js')
    os.system('%s -o ../../indico/htdocs/js/indico/pack indico.cfg' % jsbuildPath)
    os.system('%s -o ../../indico/htdocs/js/presentation/pack presentation.cfg' % jsbuildPath )
    os.chdir('../..')


def _checkModPythonIsInstalled():
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


def _checkDirPermissions(dbInstalledBySetupPy=False, uid=None, gid=None):
    '''Makes sure that directories which need write access from Apache have
    the correct permissions
    
    - dbInstalledBySetupPy if True, means that the dbdir has been created by the setup
        process and needs to be checked.
    
    - uid and gid: if they are valid user_ids and group_ids they will be used to chown
        the directories instead of the indico.conf ones. 
    '''
    from MaKaC.common.Configuration import Config
    cfg = Config.getInstance()

    # if we are on linux we need to give proper permissions to the results directory
    if sys.platform == "linux2":
        prompt = True

        # Check to see if uid/gid were provided through commandline
        if uid and gid:
            try:
                pwd.getpwuid(int(uid))
                grp.getgrgid(int(gid))
                accessuser = int(uid)
                accessgroup = int(gid)
                prompt = False
            except KeyError:
                print 'Invalid pair uid/gid (%s/%s)' % (uid, gid)

        # Try to use indico.conf's
        try:
            pwd.getpwnam(cfg.getApacheUser())
            grp.getgrnam(cfg.getApacheGroup())
            accessuser = cfg.getApacheUser()
            accessgroup = cfg.getApacheGroup()
            prompt = False
        except KeyError:
            print "\nERROR: indico.conf's ApacheUser and ApacheGroup options are incorrect (%s/%s)." % (cfg.getApacheUser(), cfg.getApacheGroup())

        if prompt == True:
            valid_credentials = False
            while not valid_credentials:
                accessuser = raw_input("\nPlease enter the user that will be running the Apache server: ")
                accessgroup = raw_input("\nPlease enter the group that will be running the Apache server: ")
                try:
                    pwd.getpwnam(accessuser)
                    grp.getgrnam(accessgroup)
                    valid_credentials = True
                except KeyError:
                    print "\nERROR: Invalid user/group pair (%s/%s)" % (accessuser, accessgroup)
                
                modifyOnDiskIndicoConfOption('%s/indico.conf' % cfg.getConfigurationDir(), 'ApacheUser', accessuser)
                modifyOnDiskIndicoConfOption('%s/indico.conf' % cfg.getConfigurationDir(), 'ApacheGroup', accessgroup)

        dirs2check = [cfg.getPublicFolder(), cfg.getLogDir(), cfg.getUploadedFilesTempDir(), cfg.getXMLCacheDir()]
        if dbInstalledBySetupPy:
            dirs2check.append(LOCALDATABASEDIR)

        for dir in dirs2check:
            print commands.getoutput("chown -R %s:%s %s" % (accessuser, accessgroup, dir))        
        

def _existingDb():
    return os.path.exists(LOCALDATABASEDIR)


def _existingIndicoConfPath():
    from MaKaC.common.Configuration import Config
    cfg = Config.getInstance() 
    return os.path.join(cfg.getConfigurationDir(), 'indico.conf')


def _existingInstallation():
    '''Returns true if an existing installation has been detected.

       We consider that an existing installation exists if there is an
       "indico.conf" file inside the directory pointed by the
       ConfigurationDir var of the "indico.conf from this directory.'''
    return os.path.exists(_existingIndicoConfPath())


def _activateIndicoConfFromExistingInstallation():
    '''Updates the MaKaCConfig file inside the directory from which we
    are installing and forces Configuration to reload its values
    '''
    from MaKaC.common.Configuration import Config
    updateIndicoConfPathInsideMaKaCConfig(_existingIndicoConfPath(),
        os.path.join(os.path.dirname(os.path.abspath(MaKaC.__file__)), 'common', 'MaKaCConfig.py'))

    Config.getInstance().forceReload()


        
def indico_pre_install(config_dir, force_upgrade=False):
    '''config_dir is the final configuration dir which will be different than
    the currently loaded Config's ''' 
    from MaKaC.common.Configuration import Config
    cfg = Config.getInstance()
        
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    
    if _existingInstallation():
        if force_upgrade:
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

What do you want to do [u/E]? ''' % _existingIndicoConfPath())
            if opt in ('', 'e', 'E'):
                print "\nExiting installation..\n"
                sys.exit()
            elif opt == 'u':
                _activateIndicoConfFromExistingInstallation()
            else:
                print "\nInvalid answer. Exiting installation..\n"
                sys.exit()

    compileAllLanguages()
    indicoconfpath = os.path.join(config_dir, 'indico.conf')
    
    if not os.path.exists(indicoconfpath):
        if not os.path.exists(PWD_INDICO_CONF):
            opt = raw_input('''
We did not detect an existing Indico installation.
We also did not detect an etc/indico.conf file in this directory.
At this point you can:

    [c]opy the default values in etc/indico.conf.sample to a new etc/indico.conf
    and continue the installation

    [A]bort the installation in order to inspect etc/indico.conf.sample
    and / or to make your own etc/indico.conf

What do you want to do [c/a]? ''')
            if opt in ('c', 'C'):
                shutil.copy(PWD_INDICO_CONF + '.sample', PWD_INDICO_CONF)
            elif opt in ('', 'a', 'A'):
                print "\nExiting installation..\n"
                sys.exit()
            else:
                print "\nInvalid anwer. Exiting installation..\n"
                sys.exit()
    
    activemakacconfig = os.path.join(os.path.dirname(os.path.abspath(MaKaC.__file__)), 'common', 'MaKaCConfig.py') 
    updateIndicoConfPathInsideMaKaCConfig(indicoconfpath, activemakacconfig)
    


def indico_post_install(config_dir, makacconfig_base_dir, package_dir, uid=None, gid=None):
    from MaKaC.common.Configuration import Config
    cfg = Config.getInstance()
    
    createDirs()
    indicoconfpath = os.path.join(config_dir, 'indico.conf')
    updateIndicoConfPathInsideMaKaCConfig(indicoconfpath, 
                                          os.path.join(makacconfig_base_dir, 'MaKaCConfig.py'))

    for f in [xx for xx in ('%s/zdctl.conf' % config_dir, 
                            '%s/zodb.conf' % config_dir) if not os.path.exists(xx)]:
        shutil.copy('%s.sample' % f, f)

    if not os.path.exists(indicoconfpath) and os.path.exists(PWD_INDICO_CONF):
        shutil.copy(PWD_INDICO_CONF, indicoconfpath)

    if os.path.exists(PWD_INDICO_CONF):
        upgrade_indico_conf(indicoconfpath, PWD_INDICO_CONF)
        
    # Shall we create a DB?
    dbInstalledBySetupPy = False
    if not _existingDb():
        opt = None
        while opt not in ('Y', 'y', 'n', ''):
            opt = raw_input('''\nWe cannot connect to the configured database at %s.

Do you want to create a new database now [Y/n]? ''' % str(cfg.getDBConnectionParams()))
            if opt in ('Y', 'y', ''):
                dbInstalledBySetupPy = True
                dbpath_ok = False
                while not dbpath_ok:
                    dbpath = raw_input('''\nWhere do you want to install the database [/opt/indico/db]? ''')
                    if dbpath.strip() == '':
                        dbpath = LOCALDATABASEDIR

                    try:
                        os.makedirs(dbpath)
                        dbpath_ok = True
                    except Exception:
                        print 'Unable to create database at %s, please make sure that you have permissions to create that directory' % dbpath

            elif opt == 'n':
                sys.exit()

    #we delete an existing vars.js.tpl.tmp
    tmp_dir = cfg.getUploadedFilesTempDir()
    varsJsTplTmpPath = os.path.join(tmp_dir, 'vars.js.tpl.tmp')
    if os.path.exists(varsJsTplTmpPath):
        print 'Old vars.js.tpl.tmp found at: %s. Removing' % varsJsTplTmpPath
        os.remove(varsJsTplTmpPath)
    

    _checkDirPermissions(dbInstalledBySetupPy=dbInstalledBySetupPy, uid=uid, gid=gid)

    _checkModPythonIsInstalled()

    print """

Congratulations!
Indico has been installed correctly.

    indico.conf:      %s/indico.conf

    BinDir:           %s
    DocumentationDir: %s
    ConfigurationDir: %s
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

Alias /indico/images "%s/images"
Alias /indico "%s"

(change the paths after 'Alias' in order to change the URL bindings)


If you are running ZODB on this host:
- Review %s/zodb.conf and %s/zdctl.conf to make sure everything is ok.
- To start the database run: zdctl.py -C %s/zdctl.conf start
""" % (cfg.getConfigurationDir(), cfg.getBinDir(), cfg.getDocumentationDir(), cfg.getConfigurationDir(), cfg.getHtdocsDir(), cfg.getHtdocsDir(), package_dir, cfg.getHtdocsDir(), cfg.getHtdocsDir(), cfg.getHtdocsDir(), cfg.getConfigurationDir(), cfg.getConfigurationDir(), cfg.getConfigurationDir())


