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
from MaKaC.conference import CategoryManager

DBMgr.getInstance().startRequest()
cm=CategoryManager()

cat=cm.getById('2l76')
conferences= cat.getAllConferenceList()
f = open("statusProtection.txt","w")
for conference in conferences:
    f.write(conference.getId() + " " + conference.getTitle() + " " + str(conference.isItselfProtected()) + " " + str(conference.isProtected())  + "\n")
f.close()
DBMgr.getInstance().endRequest()

