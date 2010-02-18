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
import pkg_resources
import copy



if sys.platform == 'linux2':
    import pwd
    import grp

import MaKaC

INDICO_INSTALL = False

LOCALDATABASEDIR = '/opt/indico/db'

# Egg directory + etc/indico.conf
PWD_INDICO_CONF = os.path.abspath(os.path.join(
    os.path.split(os.path.dirname(MaKaC.__file__))[0],'etc', 'indico.conf'
    ))

def setIndicoInstallMode(newmode):
    """
    Sets indico install mode.
    This function and getIndicoInstallMode are used by some __init__.py inside
    MaKaC to load or not some modules. At installation time those modules are not
    available. That's why we need to skip them. They are imported there only as
    shortcuts.
    """
    global INDICO_INSTALL
    INDICO_INSTALL = newmode


def getIndicoInstallMode():
    global INDICO_INSTALL
    return INDICO_INSTALL


def createDirs(directories):
    '''Creates directories that are not automatically created by setup.install or easy_install'''
    for d in ['log', 'tmp', 'cache', 'archive']:
        if not os.path.exists(directories[d]):
            os.makedirs(directories[d])

def upgrade_indico_conf(existing_conf, new_conf, mixinValues={}):
    """
    Copies new_conf values to existing_conf file preserving existing_conf's values

    If mixinValues is given its items will be preserved above existing_conf's values and new_conf's values
    """

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
            regexp = re.compile('^(%s[ ]*=[ ]*)[\{](.+)[\}$]' % k, re.MULTILINE)
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

def _updateMaKaCEggCache(file, path):
    fdata = open(file).read()
    fdata = re.sub('\/opt\/indico\/tmp', path, fdata)
    open(file, 'w').write(fdata)


def compileAllLanguages():
    '''Generates .mo files from .po files'''
    pwd = os.getcwd()
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(MaKaC.__file__)), 'po'))
    retVal = os.system('%s compile-all-lang.py --quiet' % sys.executable)

    if (retVal>>8) != 0:
        print "Generation of .mo files failed - maybe you don't have gettext installed?"
        sys.exit(-1)

    os.chdir(pwd)


def copytreeSilently(source, target):
    '''Copies source tree to target tree overwriting existing files'''
    source = os.path.normpath(source)
    target = os.path.normpath(target)
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

    try:
        pkg_resources.require('jstools')
    except pkg_resources.DistributionNotFound:
        print """
JSTools not found! JSTools is needed for JavaScript compression, if you're building Indico from source. Please install it.
i.e. try 'easy_install jstools'"""
        sys.exit(-1)

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


def _guessApacheUidGid():

    finalUser, finalGroup = None, None

    for username in ['apache', 'www-data', 'www']:
        try:
            finalUser = pwd.getpwnam(username)
            break
        except KeyError:
            pass

    for groupname in ['apache', 'www-data', 'www']:
        try:
            finalGroup = grp.getgrnam(groupname)
            break
        except KeyError:
            pass

    return finalUser, finalGroup

def _findApacheUserGroup(uid, gid):
        # if we are on linux we need to give proper permissions to the results directory
    if sys.platform == "linux2":
        prompt = True

        # Check to see if uid/gid were provided through commandline
        if uid and gid:
            try:
                accessuser = pwd.getpwuid(int(uid)).pw_name
                accessgroup = grp.getgrgid(int(gid)).gr_name
                prompt = False
            except KeyError:
                print 'uid/gid pair (%s/%s) provided through command line is false' % (uid, gid)
        else:
            print "uid/gid not provided. Trying to guess them... ",
            uid, gid = _guessApacheUidGid()
            if uid and gid:
                print "found %s(%s) %s(%s)" % (uid.pw_name, uid.pw_uid,
                                         gid.gr_name, gid.gr_gid)
                accessuser = uid.pw_name
                accessgroup = gid.gr_name
                prompt = False

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

        return accessuser, accessgroup


def _checkDirPermissions(directories, dbInstalledBySetupPy=False, accessuser=None, accessgroup=None):
    '''Makes sure that directories which need write access from Apache have
    the correct permissions

    - dbInstalledBySetupPy if True, means that the dbdir has been created by the setup
        process and needs to be checked.

    - uid and gid: if they are valid user_ids and group_ids they will be used to chown
        the directories instead of the indico.conf ones.
    '''

    print "\nWe need to 'sudo' in order to set the permissions of some directories..."

    dirs2check = list(directories[x] for x in ['htdocs', 'log', 'tmp', 'cache', 'archive'])
    if dbInstalledBySetupPy:
        dirs2check.append(dbInstalledBySetupPy)

    for dir in dirs2check:
        print commands.getoutput("if test $(which sudo); then CMD=\"sudo\"; fi; $CMD chown -R %s:%s %s" % (accessuser, accessgroup, dir))


def _existingConfiguredEgg():
    '''Returns true if an existing EGG has been detected.'''

    # remove '.' and './indico'
    path = copy.copy(sys.path)
    path = path[2:]

    env = pkg_resources.Environment(search_path=path)
    env.scan(search_path=path)

    # search for all indico dists
    indico_dists = env['cds-indico']

    for dist in indico_dists:
        eggPath = dist.location

        print "* EGG found at %s..." % eggPath,
        fdata = open(os.path.join(eggPath,'MaKaC','common','MaKaCConfig.py'), 'r').read()

        m = re.search('^\s*indico_conf\s*=\s*[\'"]{1}([^\'"]*)[\'"]{1}', fdata, re.MULTILINE)
        if m and m.group(1) != '':
            print '%s' % m.group(1)
            return m.group(1)
        else:
            print 'unconfigured'
    return None

def _extractDirsFromConf(conf):
    execfile(conf)
    values = locals().copy()

    return {'bin': values['BinDir'],
            'doc': values['DocumentationDir'],
            'etc': values['ConfigurationDir'],
            'htdocs': values['HtdocsDir'],
            'tmp': values['UploadedFilesTempDir'],
            'log': values['LogDir'],
            'cache': values['XMLCacheDir'],
            'archive': values['ArchiveDir'],
            'db': LOCALDATABASEDIR}

def _replacePrefixInConf(filePath, prefix):
    fdata = open(filePath).read()
    fdata = re.sub('\/opt\/indico', prefix, fdata)
    open(filePath, 'w').write(fdata)

def _updateDbConfigFiles(dbDir, logDir, cfgDir, tmpDir, uid):
    filePath = os.path.join(cfgDir, 'zodb.conf')
    fdata = open(filePath).read()
    fdata = re.sub('\/opt\/indico\/db', dbDir, fdata)
    fdata = re.sub('\/opt\/indico\/log', logDir, fdata)
    open(filePath, 'w').write(fdata)

    filePath = os.path.join(cfgDir, 'zdctl.conf')
    fdata = open(filePath).read()
    fdata = re.sub('\/opt\/indico\/db', dbDir, fdata)
    fdata = re.sub('\/opt\/indico\/etc', cfgDir, fdata)
    fdata = re.sub('\/opt\/indico\/tmp', tmpDir, fdata)
    fdata = re.sub('(\s+user\s+)apache', '\g<1>%s' % uid, fdata)
    open(filePath, 'w').write(fdata)


def indico_pre_install(defaultPrefix, force_upgrade=False, existingConfig=None):
    """
    defaultPrefix is the default prefix dir where Indico will be installed
    """

    upgrade = False

    # Configuration specified in the command-line
    if existingConfig:
        existing = existingConfig
        # upgrade is mandatory
        upgrade = True
    else:
        # Config not specified
        # automatically find an EGG in the site-packages path
        existing = _existingConfiguredEgg()

        # if an EGG was found but upgrade is not forced
        if existing and not force_upgrade:

            # Ask the user
            opt = None

            while opt not in ('', 'e', 'E', 'u'):
                opt = raw_input('''
An existing Indico configuration has been detected at:

    %s

At this point you can:

    [u]pgrade the existing installation

    [E]xit this installation process

What do you want to do [u/E]? ''' % existing)
            if opt in ('', 'e', 'E'):
                print "\nExiting installation..\n"
                sys.exit()
            elif opt == 'u':
                upgrade = True
            else:
                print "\nInvalid answer. Exiting installation..\n"
                sys.exit()
        # if and EGG was found and upgrade is forced
        elif existing and force_upgrade:
            upgrade = True

    if upgrade:
        print 'Upgrading the existing Indico installation..'
        return _extractDirsFromConf(existing)
    else:
        # then, in case no previous installation exists
        return fresh_install(defaultPrefix)


def fresh_install(defaultPrefix):

    # start from scratch
    print "No previous installation of Indico was found."
    print "Please specify a directory prefix:"

    # ask for a directory prefix
    prefixDir = raw_input('[%s]: ' % defaultPrefix).strip()

    if prefixDir == '':
        prefixDir = defaultPrefix

    configDir = os.path.join(prefixDir, 'etc')

    # create the directory that will contain the configuration files
    if not os.path.exists(configDir):
            os.makedirs(configDir)

    # compile po -> mo
    compileAllLanguages()

    indicoconfpath = os.path.join(configDir, 'indico.conf')

    opt = raw_input('''
You now need to configure Indico, by editing indico.conf or letting us do it for you.
At this point you can:

    [c]opy the default values in etc/indico.conf.sample to a new etc/indico.conf
    and continue the installation

    [A]bort the installation in order to inspect etc/indico.conf.sample
    and / or to make your own etc/indico.conf

What do you want to do [c/a]? ''')
    if opt in ('c', 'C'):
        shutil.copy(PWD_INDICO_CONF + '.sample', indicoconfpath)
        _replacePrefixInConf(indicoconfpath, prefixDir)
    elif opt in ('', 'a', 'A'):
        print "\nExiting installation..\n"
        sys.exit()
    else:
        print "\nInvalid answer. Exiting installation..\n"
        sys.exit()

    activemakacconfig = os.path.join(os.path.dirname(os.path.abspath(MaKaC.__file__)), 'common', 'MaKaCConfig.py')
    updateIndicoConfPathInsideMaKaCConfig(indicoconfpath, activemakacconfig)

    return dict((dirName, os.path.join(prefixDir, dirName))
                for dirName in ['bin','doc','etc','htdocs','tmp','log','cache','db','archive'])


def indico_post_install(targetDirs, sourceDirs, makacconfig_base_dir, package_dir, force_no_db = False, uid=None, gid=None, dbDir=LOCALDATABASEDIR):
    from MaKaC.common.Configuration import Config

    if 'db' in targetDirs:
        # we don't want that the db directory be created
        dbDir = targetDirs['db']
        del targetDirs['db']

    print "Creating directories for resources... ",
    # Create the directories where the resources will be installed
    createDirs(targetDirs)
    print "done!"

    # target configuration file (may exist or not)
    newConf = os.path.join(targetDirs['etc'],'indico.conf')
    # source configuration file (package)
    sourceConf = os.path.join(sourceDirs['etc'], 'indico.conf.sample')

    # if there is a source config
    if os.path.exists(sourceConf):
        if not os.path.exists(newConf):
            # just copy if there is no config yet
            shutil.copy(sourceConf, newConf)
        else:
            print "Upgrading indico.conf...",
            # upgrade the existing one
            upgrade_indico_conf(newConf, sourceConf)
            print "done!"

    # change MaKaCConfig.py to include the config
    updateIndicoConfPathInsideMaKaCConfig(newConf,
                                          os.path.join(makacconfig_base_dir, 'MaKaCConfig.py'))

    # copy the db config files
    for f in [xx for xx in ('%s/zdctl.conf' % targetDirs['etc'],
                            '%s/zodb.conf' % targetDirs['etc']) if not os.path.exists(xx)]:
        shutil.copy('%s.sample' % f, f)

    # Shall we create a DB?
    dbInstalledBySetupPy = False
    dbpath = None

    if force_no_db:
        print 'Skipping database detection'
    else:
        if os.path.exists(dbDir):
            dbpath = dbDir
            print 'Successfully found a database directory at %s' % dbDir
        else:
            opt = None
            while opt not in ('Y', 'y', 'n', ''):
                opt = raw_input('''\nWe cannot find a configured database at %s.

    Do you want to create a new database now [Y/n]? ''' % dbDir)
                if opt in ('Y', 'y', ''):
                    dbInstalledBySetupPy = True
                    dbpath_ok = False
                    while not dbpath_ok:
                        dbpath = raw_input('''\nWhere do you want to install the database [%s]? ''' % dbDir)
                        if dbpath.strip() == '':
                            dbpath = dbDir

                        try:
                            os.makedirs(dbpath)
                            dbpath_ok = True
                        except Exception, e:
                            print e
                            print 'Unable to create database at %s, please make sure that you have permissions to create that directory' % dbpath

                elif opt == 'n':
                    pass

    #we delete an existing vars.js.tpl.tmp
    tmp_dir = targetDirs['tmp']

    varsJsTplTmpPath = os.path.join(tmp_dir, 'vars.js.tpl.tmp')
    if os.path.exists(varsJsTplTmpPath):
        print 'Old vars.js.tpl.tmp found at: %s. Removing' % varsJsTplTmpPath
        os.remove(varsJsTplTmpPath)

    if dbInstalledBySetupPy:
        dbParam = dbpath
    else:
        dbParam = None

    # find the apache user/group
    user, group = _findApacheUserGroup(uid, gid)

    # change indico.conf
    modifyOnDiskIndicoConfOption('%s/indico.conf' % targetDirs['etc'], 'ApacheUser', user)
    modifyOnDiskIndicoConfOption('%s/indico.conf' % targetDirs['etc'], 'ApacheGroup', group)

    # set the directory for the egg cache
    _updateMaKaCEggCache(os.path.join(package_dir, 'MaKaC', '__init__.py'), targetDirs['tmp'])

    if not force_no_db and dbpath:
        # change the db config files (paths + apache user/group)
        _updateDbConfigFiles(dbpath, targetDirs['log'], targetDirs['etc'], targetDirs['tmp'], user)

    # check permissions
    _checkDirPermissions(targetDirs, dbInstalledBySetupPy=dbParam, accessuser=user, accessgroup=group)
    # check that mod_python is installed
    _checkModPythonIsInstalled()

    print """

Congratulations!
Indico has been installed correctly.

    indico.conf:      %s/indico.conf

    BinDir:           %s
    DocumentationDir: %s
    ConfigurationDir: %s
    HtdocsDir:        %s

For information on how to configure Apache HTTPD, take a look at:

http://cdswaredev.cern.ch/indico/wiki/Admin/Installation#ConfiguringApache


Please do not forget to start the 'taskDaemon' in order to use alarms, creation
of off-line websites, reminders, etc. You can find it in './bin/taskDaemon.py'

%s
""" % (targetDirs['etc'], targetDirs['bin'], targetDirs['doc'], targetDirs['etc'], targetDirs['htdocs'], _databaseText(targetDirs['etc']))

def _databaseText(cfgPrefix):
    return """If you are running ZODB on this host:
 - Review %s/zodb.conf and %s/zdctl.conf to make sure everything is ok.
 - To start the database run: zdaemon -C %s/zdctl.conf start
""" % (cfgPrefix, cfgPrefix, cfgPrefix)
