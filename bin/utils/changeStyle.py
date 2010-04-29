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

from MaKaC.common import DBMgr
from MaKaC.webinterface import displayMgr
from MaKaC.conference import CategoryManager

logfile=open('./oldstyles','w')
def changeCatStyle(cat):
    for subcat in cat.getSubCategoryList():
        currentStyle=subcat.getDefaultStyle("meeting")
        subcat.setDefaultStyle("meeting", "lhcb_meeting")
        logfile.write("cat %s: %s"%(subcat.getId(), currentStyle))
        changeCatStyle(subcat)
    for conf in cat.getConferenceList():
        currentStyle=displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(conf).getDefaultStyle()
        displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(conf).setDefaultStyle("lhcb_meeting")
        logfile.write("\t\t\tconf %s: %s"%(conf.getId(), currentStyle))


dbm = DBMgr.getInstance()
dbm.startRequest()
cat=CategoryManager().getById('233')
currentStyle=cat.getDefaultStyle("meeting")
cat.setDefaultStyle("meeting", "lhcb_meeting")
logfile.write("cat %s: %s"%(cat.getId(), currentStyle))
changeCatStyle(cat)

dbm.endRequest()

