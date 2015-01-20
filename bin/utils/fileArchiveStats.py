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

"""
Calculates total size of archive and number of files
"""

from indico.core.db import DBMgr
from MaKaC.conference import LocalFile, ConferenceHolder
from indico.util.console import conferenceHolderIterator


def main():
    dbi = DBMgr.getInstance()

    dbi.startRequest()

    ch = ConferenceHolder()

    totalSize = 0
    fNumber = 0

    for __, obj in conferenceHolderIterator(ch, verbose=True):
        for material in obj.getAllMaterialList():
            for res in material.getResourceList():
                if isinstance(res, LocalFile):
                    try:
                        totalSize += res.getSize()
                        fNumber += 1
                    except OSError:
                        print "Problems stating size of '%s'" % res.getFilePath()

    dbi.endRequest(False)

    print "%d files, %d bytes total" % (fNumber, totalSize)
    print "avg %s bytes/file" % (float(totalSize) / fNumber)


if __name__ == '__main__':
    main()
