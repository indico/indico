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

import sys
sys.path.append("c:/MaKaC/indico/code/code")

from indico.core.db import DBMgr

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
