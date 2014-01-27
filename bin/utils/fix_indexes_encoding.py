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

from MaKaC.common.indexes import IndexesHolder
from indico.util.string import fix_broken_string
from indico.core.db import DBMgr


INDEXES = ["name", "surName"]


def fix_indexes():
    dbi = DBMgr.getInstance()
    dbi.startRequest()

    ih = IndexesHolder()

    for idx_name in INDEXES:
        idx = ih.getById(idx_name)
        words = idx._words
        for key in words.iterkeys():
            newKey = fix_broken_string(key)
            values = words[key]
            del words[key]
            words[newKey] = values
        idx.setIndex(words)
        dbi.commit()

    dbi.endRequest()


if __name__ == '__main__':
    fix_indexes()
