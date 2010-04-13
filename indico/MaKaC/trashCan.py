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

import time
from MaKaC.common.ObjectHolders import ObjectHolder
from MaKaC.i18n import _

class TrashCanManager(ObjectHolder):
    idxName = "trashcan"
    
    def add(self, newItem):
        oid = ""
        try:
            oid = newItem._p_oid            
        except:
            raise MaKaCError( _("Cannot put an object which is not persistent in the trash can."))
        tree = self._getIdx()
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
