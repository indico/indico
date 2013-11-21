# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

from MaKaC.user import GroupHolder
from MaKaC.conference import CategoryManager
from MaKaC.webinterface.urlHandlers import UHCategoryDisplay, UHConferenceDisplay

from indico.core.db import DBMgr


def checkGroup (obj, group):
    ac = obj.getAccessController()
    if group in ac.allowed:
        return True
    return False

def showSubCategory(cat, group):
    if checkGroup(cat, group):
        print "%s - %s"%(cat.getName(), UHCategoryDisplay.getURL(cat))
    if cat.hasSubcategories():
        for subcat in cat.getSubCategoryList():
            showSubCategory(subcat,group)
    else:
        for conference in  cat.getConferenceList():
           if checkGroup(conference, group):
               print "%s - %s"%(conference.getName(), UHConferenceDisplay.getURL(conference))

DBMgr.getInstance().startRequest()
cm=CategoryManager()
cat=cm.getById("XXXX")
group = GroupHolder().getById("YYYYY")
showSubCategory(cat, group)


DBMgr.getInstance().endRequest()
