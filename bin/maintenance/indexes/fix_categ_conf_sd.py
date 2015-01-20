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

"""
Checks consistency (fixing errors) of 'categ_conf_sd'
"""


from indico.core.index import Catalog

from indico.core.db import DBMgr
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
