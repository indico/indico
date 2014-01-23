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
'''This script will need to be called after doing easy_install indico to
complete the installation process.

It only contains functions specific to easy_install. For the rest of the
functions refer to installBase.py

On RPM or windist based installations it can be made run automatically'''

import os, sys
import shutil, getopt

from distutils.sysconfig import get_python_lib

from installBase import getIndicoInstallMode, setIndicoInstallMode, PWD_INDICO_CONF, indico_pre_install, indico_post_install, copyTreeSilently

# The directory where the egg is located
eggDir = os.path.join(os.path.dirname(__file__), '..', '..')

def copy_egg_datafiles_to_base(dstDir):
    """Copies bin, doc, etc & htdocs from egg's installation folder to dstDir
    NOTE: the egg is always uncompressed because we make references to __file__ all over the place.
    """
    global eggDir

    binDir = os.path.join(eggDir, 'bin')
    docDir = os.path.join(eggDir, 'doc')
    cfgDir = os.path.join(eggDir, 'etc')
    htdocsDir = os.path.join(eggDir, 'htdocs')

    for (dst, src) in ((dstDir['bin'], binDir), (dstDir['doc'], docDir), (dstDir['etc'], cfgDir), (dstDir['htdocs'], htdocsDir)):
        print "%s -> %s" % (src, dst)
        if (os.path.exists(dst) and not os.access(dst, os.W_OK)):
            print "You don't have write permissions for directory %s!" % dst
            print "Aborting."
            sys.exit(-1)
        copyTreeSilently(src, dst)


def main():

    global PWD_INDICO_CONF
    global eggDir

    optlist, args = getopt.getopt(sys.argv[1:],'',['rpm','existing-config=',
                                                   'www-uid=','www-gid='])

    wwwUid = None
    wwwGid = None

    forRPM = False
    existingPath = None

    for o,a in optlist:
        if o == '--rpm':
            forRPM = True
        elif o == '--existing-config':
            existingPath = a
        elif o == "--www-uid":
            wwwUid = a
        elif o == "--www-gid":
            wwwGid = a

    setIndicoInstallMode(True)

    if forRPM:
        # TODO: post-install for RPMs
        pass
    else:
        targetDirs = { 'etc': '/opt/indico/etc' }
        PWD_INDICO_CONF = os.path.join(os.path.dirname(__file__), '..', '..', 'etc', 'indico.conf.sample')

        targetDirs = indico_pre_install('/opt/indico', False, existingConfig=existingPath)
        # we need to copy htdocs/ bin/ doc/ etc/ to its proper place
        print "Copying Indico tree... "
        copy_egg_datafiles_to_base(targetDirs)
        if hasattr(os, 'symlink'):
            wsgi_file = os.path.join(targetDirs['htdocs'], 'indico.wsgi')
            print "Creating wsgi symlink... %s" % wsgi_file
            if os.path.exists(wsgi_file):
                os.unlink(wsgi_file)
            os.symlink(os.path.join(eggDir, 'indico/web/indico.wsgi'), wsgi_file)
        print "done!"


    sourceDirs = dict((dirName, os.path.join(eggDir, dirName))
                      for dirName in ['bin','doc','etc','htdocs'])

    indico_post_install(targetDirs,
                        sourceDirs,
                        os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                     '..',
                                     'common'),
                        eggDir,
                        force_no_db=(existingPath != None),
                        uid = wwwUid,
                        gid = wwwGid)

if __name__ == '__main__':
    main()
