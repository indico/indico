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

from MaKaC.common import DBMgr
from MaKaC.conference import CategoryManager
from MaKaC.common import indexes


def main():
    """
    This script deletes existing category indexes and recreates them.
    """

    dbi = DBMgr.getInstance()
    dbi.startRequest()

    im = indexes.IndexesHolder()
    im.removeById('categoryDate')
    catIdx = im.getIndex('categoryDate')

    cm = CategoryManager()
    num_categs = len(cm._getIdx())
    cur_num = cur_percent = 0

    for cat in cm._getIdx().itervalues():
        for conf in cat.conferences.itervalues():
            catIdx.indexConf(conf)
        dbi.commit()

        cur_num += 1
        percent = int(float(cur_num) / num_categs * 100)
        if percent != cur_percent:
            cur_percent = percent
            print "{0}%".format(percent)
    dbi.endRequest()


if __name__ == "__main__":
    main()
