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
from MaKaC.common.indexes import IndexesHolder
from indico.core.index import Catalog


if __name__ == '__main__':

    dbi = DBMgr.getInstance()

    dbi.startRequest()

    for idx_name in ['categ_conf_sd']:
        idx = Catalog.getIdx(idx_name)
        for problem in idx._check(dbi=dbi):
            print "[%s] %s" % (idx_name, problem)

    for idx_name in ['category', 'calendar', 'categoryDate']:
        idx = IndexesHolder().getIndex(idx_name)
        for problem in idx._check(dbi=dbi):
            print "[%s] %s" % (idx_name, problem)

    dbi.endRequest()
