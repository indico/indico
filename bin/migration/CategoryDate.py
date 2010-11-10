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

import sys
from datetime import datetime

from MaKaC.common.db import DBMgr
from MaKaC.common.indexes import IndexesHolder, CategoryDayIndex

def switchIndex():
    if IndexesHolder()._getIdx().has_key("backupCategoryDate") and IndexesHolder()._getIdx().has_key("categoryDate"):
        tmp = IndexesHolder()._getIdx()["backupCategoryDate"]
        IndexesHolder()._getIdx()["backupCategoryDate"] = IndexesHolder().getIndex("categoryDate")
        IndexesHolder()._getIdx()["categoryDate"] = tmp
        print "Index was switched"
    else:
        print "Cannot switch indexes."

def migrateCategoryDateIndex():
    IndexesHolder()._getIdx()["backupCategoryDate"] = IndexesHolder().getIndex("categoryDate")
    newIdx = CategoryDayIndex()
    newIdx.buildIndex()
    IndexesHolder()._getIdx()["categoryDate"] = newIdx
    print "Migration was successful"

def displayIndexes():
    for idx in IndexesHolder()._getIdx():
        print str(idx) + " " + str(IndexesHolder()._getIdx()[str(idx)])

def deleteBackup():
    if IndexesHolder()._getIdx().has_key("backupCategoryDate"):
        del IndexesHolder()._getIdx()["backupCategoryDate"]
        print "Backup deleted."
    else:
        print "Backup not found"

def main(argv):
    DBMgr.getInstance().startRequest()

    print "Req start at " + str(datetime.now())

    if "migrate" in argv:
        migrateCategoryDateIndex()
    if "switch" in argv:
        switchIndex()
    if "removeBackup" in argv:
        deleteBackup()
    if "display" in argv:
        displayIndexes()

    print "Req ends at " + str(datetime.now())
    DBMgr.getInstance().endRequest()

if __name__ == "__main__":
    sys.exit(main(sys.argv))