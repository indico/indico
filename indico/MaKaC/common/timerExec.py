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

# XXX: This file is OBSOLETE, it is just kept in case someone needs to migrate from an extremely ancient version!

from BTrees import OOBTree
from persistent import Persistent

from indico.core.db import DBMgr


class taskList(Persistent):
    def getTasks(self):
        return self.listTask.values()

class HelperTaskList:
    @classmethod
    def getTaskListInstance(cls):
        root = DBMgr.getInstance().getDBConnection().root()
        try:
            tlist = root["taskList"]["main"]
        except KeyError, e:
            tlist = taskList()
            root["taskList"] = OOBTree.OOBTree()
            root["taskList"]["main"] = tlist
        return tlist


class task(Persistent):
    pass


class obj(Persistent):
    pass


class sendMail(obj):
    pass


class FoundationSync(obj):
    pass


class Alarm(task):
    pass


class StatisticsUpdater(obj):
    pass
