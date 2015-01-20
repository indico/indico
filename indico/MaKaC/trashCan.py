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

import time
from MaKaC.common.ObjectHolders import ObjectHolder
from MaKaC.i18n import _
from indico.util.contextManager import ContextManager

class TrashCanManager(ObjectHolder):
    idxName = "trashcan"

    def add(self, newItem):
        oid = ""
        try:
            oid = newItem._p_oid
        except:
            raise MaKaCError( _("Cannot put an object which is not persistent in the trash can."))
        tree = self._getIdx()
        if not (ContextManager.get('test_env')):
            tree[oid] = newItem

    def remove(self, item):
        oid = ""
        try:
            oid = item._p_oid
        except:
            return
        tree = self._getIdx()
        if not tree.has_key(oid):
            return
        del tree[oid]

    def emptyTrashCan(self, dt):
    # Remove all the objects whose modification date is less than dt.
        ts = time.mktime(dt.timetuple())
        for i in self.getValuesToList():
            if i._p_mtime < ts:
                self.remove(i)
