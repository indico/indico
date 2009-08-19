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
'''This script will need to be called after doing easy_install cds-indico to
complete the installation process.

It only contains functions specific to easy_install. For the rest of the 
functions refer to installBase.py 

On RPM or windist based installations it can be made run automatically'''
import os
import shutil

from distutils.sysconfig import get_python_lib

from installBase import getIndicoInstallMode, setIndicoInstallMode, PWD_INDICO_CONF, indico_pre_install, indico_post_install, copytreeSilently


def copy_egg_datafiles_to_base(dstDir):
    '''Copies bin, doc, etc & htdocs from egg's installation folder to dstDir
    
    NOTE: the egg is always uncompressed because we make references to __file__ all over the place.'''
    from MaKaC.common.Configuration import Config
    cfg = Config.getInstance()
    
    for (s, dst) in (('bin', cfg.getBinDir()), ('doc', cfg.getDocumentationDir()), ('etc', cfg.getConfigurationDir()), ('htdocs', cfg.getHtdocsDir())):
        src = os.path.join(os.path.dirname(__file__), '..', '..', s)
        copytreeSilently(src, dst)


def main():
    setIndicoInstallMode(True)
    global PWD_INDICO_CONF
    PWD_INDICO_CONF = os.path.join(os.path.dirname(__file__), '..', '..', 'etc', 'indico.conf.sample')
    # we need to copy htdocs/ bin/ doc/ etc/ to its proper place
    # TODO accept commandline switches (for tests)
    copy_egg_datafiles_to_base('/opt/indico')
    if not os.path.exists('/opt/indico/etc/indico.conf'):
        shutil.copy('/opt/indico/etc/indico.conf.sample', '/opt/indico/etc/indico.conf')
        
    indico_pre_install('/opt/indico/etc', False)
    
    indico_post_install('/opt/indico/etc', os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'common'), get_python_lib(), None, None)
    