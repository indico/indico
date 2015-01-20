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

import os, shutil, re, time
from os.path import isdir, getsize, join, isfile
from MaKaC.i18n import _

class MaintenanceMng:
    dirMatch = ""
    fileMatch = "((^Indico.*)|(.*\.tmp$))"
    tmpDelay = 3*3600

    def humanReadableSize(bytes, units="b"):
            if units == 'k':
                return '%-8ldKB' % (bytes / 1024)
            elif units == 'm':
                return '%-5ldMB' % (bytes / 1024 / 1024)
            return '%-11ldbytes' % (bytes)
    humanReadableSize = staticmethod(humanReadableSize)

    def getStat(start):
        total = 0
        nFiles = 0
        nDirs = 0
        if not isdir(start):
            print _("Cannot list directory %s") % start
        else:
            for root, dirs, files in os.walk(start):
                total += sum([getsize(join(root, name)) for name in files])
                nFiles += len(files)
                nDirs += len(dirs)
        return (MaintenanceMng.humanReadableSize(total,'m'), nFiles, nDirs)
    getStat = staticmethod(getStat)

    def _match(match, filename):
        m = re.match(match, filename)
        if m:
            return True
        return False
    _match = staticmethod(_match)

    def cleanupTmp(cls, top):
        for filename in os.listdir(top):
            file = join(top,filename)
            if ( time.time() - os.path.getctime(file) ) > cls.tmpDelay:
                if isdir(file) and cls.dirMatch is not None and \
                        cls.dirMatch != "" and cls._match(cls.dirMatch, filename):
                    shutil.rmtree(file)
                elif isfile(file) and cls.fileMatch is not None and \
                        cls.fileMatch != "" and cls._match(cls.fileMatch, filename):
                    os.remove(file)
    cleanupTmp = classmethod(cleanupTmp)
