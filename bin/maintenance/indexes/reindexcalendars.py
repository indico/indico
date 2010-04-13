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

from MaKaC.common.general import *
from MaKaC.common.db import DBMgr
from MaKaC.conference import CategoryManager
from MaKaC.common import indexes
from datetime import datetime

def main():
    DBMgr.getInstance().startRequest()
    im = indexes.IndexesHolder()
    im.removeById('calendar')
    DBMgr.getInstance().commit()
    ch = CategoryManager()
    list = ch.getList()
    totnum = len(list)
    curnum = 0
    curper = 0
    for cat in list:
        committed = False
        DBMgr.getInstance().sync()
        calindex = im.getIndex('calendar')
        while not committed:
            try:
                del cat._calIdx
            except:
                pass
            for conf in cat.getConferenceList():
                calindex.indexConf(conf)
            try:
                DBMgr.getInstance().commit()
                committed = True
            except:
                DBMgr.getInstance().abort()
                print "retry %s" % cat.getId()
        curnum += 1
        per = int(float(curnum)/float(totnum)*100)
        if per != curper:
            curper = per
            if per in [0,10,20,30,40,50,60,70,80,90,100]:
                print "done %s%%" % per
    DBMgr.getInstance().endRequest()

if __name__ == "__main__":
    main()
