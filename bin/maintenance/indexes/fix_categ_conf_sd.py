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

"""
Checks consistency (fixing errors) of 'categ_conf_sd'
"""


from indico.core.index import Catalog

from MaKaC.common import DBMgr
from MaKaC.conference import CategoryManager

if __name__ == '__main__':
    dbi = DBMgr.getInstance()

    dbi.startRequest()

    index = Catalog.getIdx('categ_conf_sd')

    i = 0

    for cid, categ in CategoryManager()._getIdx().iteritems():
        catIdx = index.getCategory(cid)
        for conf in categ.conferences:
            if not catIdx.has_obj(conf):
                print "'%s' not indexed " % conf,
                catIdx.index_obj(conf)
                print "[FIXED]"
                dbi.commit()

        todelete = []
        for cid, conf in catIdx.iteritems():
            if conf not in categ.conferences:
                print "'%s' indexed " % conf,
                todelete.append(conf)
                print "[FIXED]"

        for conf in todelete:
            catIdx.unindex_obj(conf)
            dbi.commit()

        if i % 10 == 9:
            dbi.abort()
        i += 1

    dbi.endRequest()
