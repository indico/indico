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

from indico.core.db import DBMgr
from MaKaC.user import Group
from MaKaC.conference import CategoryManager

DBMgr.getInstance().startRequest()
cm=CategoryManager()

catcounter = 0
mgrscounter = 0
notSendTo={}
catList=[]
rootCatList=[]
rootCatList.append(cm.getById('1l28'))
rootCatList.append(cm.getById('1l30'))
for cat in rootCatList:
    for scat in cat.getSubCategoryList():
        catList.append(scat)

for cat in catList:
    ml = cat.getManagerList()
    if ml:
        l=[]
        for mng in ml:
            if isinstance(mng, Group):
                if notSendTo.has_key(cat.getId()):
                    notSendTo[cat.getId()].append(mng.getName())
                else:
                    notSendTo[cat.getId()]=[]
                    notSendTo[cat.getId()].append(mng.getName())
            else:
                l.append(mng)
        mln = ", ".join(["%s <%s>"%(mng.getFullName(),mng.getEmail()) for mng in l])
        print "[%s]%s\n\t--> [%s]\n"%(cat.getId(), cat.getTitle(), mln)
        catcounter += 1
        mgrscounter += len(ml)
print "%s categories with managers. There is a total of %s managers"%(catcounter, mgrscounter)
print "not send to:%s"%notSendTo
DBMgr.getInstance().endRequest()

