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


from MaKaC.common.general import *
from MaKaC.common import db
from MaKaC.conference import CategoryManager
from MaKaC.common import indexes
import transaction

def main():
    """This script deletes existing category indexes and recreates them."""
    dbi = db.DBMgr.getInstance()
    dbi.startRequest()
    im = indexes.IndexesHolder()
    im.removeById('categoryName')
    catIdx = im.getIndex('categoryName')
    ch = CategoryManager()
    totnum = len(ch.getList())
    curnum = 0
    curper = 0
    for cat in ch.getList():
        while 1:
            print cat.getId(), cat.getTitle()
            catIdx.index(cat.getId(), cat.getTitle().decode('utf-8'))
            dbi.commit()
            break
        curnum += 1
        per = int(float(curnum)/float(totnum)*100)
        if per != curper:
            curper = per
            print "%s%%" % per
    dbi.endRequest()


if __name__ == "__main__":
    main()
