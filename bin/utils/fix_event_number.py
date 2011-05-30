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

from MaKaC.common.db import DBMgr
from MaKaC.conference import CategoryManager
from ZODB.POSException import ConflictError


def _visit(dbi, cat, deep=0):
    global i

    for retries in xrange(0,10):
        try:
            if not cat.getConferenceList():
                for scat in cat.getSubCategoryList():
                    _visit(dbi, scat, deep + 1)
                cat._setNumConferences()
                print "%sset %s: %s" % (" " * deep, cat.getTitle(), cat.getNumConferences())
            dbi.commit()
            break
        except ConflictError:
            dbi.sync()

if __name__ == '__main__':
    dbi = DBMgr.getInstance()
    dbi.startRequest()
    home = CategoryManager().getById(0)

    with dbi.transaction() as conn:
        i = 0
        _visit(dbi, home)
