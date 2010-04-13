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
sys.path.append("c:/MaKaC/indico/code/code")

from MaKaC.common import DBMgr

def changePath(base, path):
    if path[:len(base)] == base:
        #the path start with the base, so remove it
        newPath = path[len(base):]
    else:
        #the path don't start with the base
        newPath = path
    while newPath[0] in ["\\", "/"]:
        #remove the / or \\ add by the os.path.join function
        newPath = newPath[1:]
    return newPath



def getRepository():
        dbRoot = DBMgr.getInstance().getDBConnection().root()
        try:
            fr = dbRoot["local_repositories"]["main"]
        except KeyError, e:
            fr = fileRepository.MaterialLocalRepository()
            dbRoot["local_repositories"] = OOBTree.OOBTree()
            dbRoot["local_repositories"]["main"] = fr
        return fr


DBMgr.getInstance().startRequest()
rep = getRepository()
list = rep.getFiles()
base = rep.getRepositoryPath()

for i in list.keys():
    list[i] = changePath(base, list[i])



DBMgr.getInstance().endRequest()
