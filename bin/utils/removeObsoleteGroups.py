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
from MaKaC.user import GroupHolder

"""
Set as obsolete the groups listed in a file
"""

fileGroups='GroupsDeletedInAD.txt'

DBMgr.getInstance().startRequest()
error = False
gh = GroupHolder()
groupIdx=gh._getIdx()

groupsObsoletes = open(fileGroups,'r')
for group in groupsObsoletes.readlines():
    gr=groupIdx.get(group.rstrip())
    if gr != None:
        gr.setObsolete(True)

if not error:
    DBMgr.getInstance().endRequest()
    print "Groups set as obsoleted."
    print "No error. The change are saved"
else:
    print "There were errors. The changes was not saved"

