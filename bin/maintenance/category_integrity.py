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
This simple script checks whether the `_numConferences` attribute is consistent for
every category, and fixs them otherwise.

It can be added as a periodic cronjob.
"""

import sys

from indico.core.db import DBMgr
from MaKaC.conference import CategoryManager, ConferenceHolder



def set_num_conferences(categ, num):
    categ._numConferences = num


def check_event_number_consistency(root):

    for categ in root.subcategories.itervalues():
        check_event_number_consistency(categ)

    if root.conferences:
        return
    else:
        total = 0
        for scat in root.subcategories.itervalues():
            total += scat._numConferences
        if root._numConferences != total:
            sys.stderr.write("(n) '%s': expected %d, got %d! " % (root.getId(), total, root._numConferences))
            set_num_conferences(root, total)
            sys.stderr.write("[FIXED]\n")
            dbi.commit()


def check_event_number_leaves(categ, expected, dbi):
    obtained = categ._numConferences

    if expected != obtained:
        # something is wrong!
        sys.stderr.write( "(l) '%s': expected %d, got %d! " % (cid, expected, obtained))

        # fix it
        set_num_conferences(categ, expected)
        sys.stderr.write("[FIXED]\n")
        dbi.commit()


if __name__ == '__main__':
    dbi = DBMgr.getInstance()
    dbi.startRequest()

    confIndex = ConferenceHolder()._getIdx()
    index = CategoryManager()._getIdx()

    for cid, categ in index.iteritems():
        # conferece-containing categories
        if categ.conferences:

            # since we're here check consistency of TreeSet
            categ.conferences._check()

            lenConfs = 0
            for conf in categ.conferences:
                lenConfs += 1
                if conf.getId() not in confIndex:
                    sys.stderr.write("[%s] '%s' not in ConferenceHolder!\n" % (cid, conf.getId()))

            # check event numbers
            check_event_number_leaves(categ, lenConfs, dbi)

            # check that there are no subcategories
            if categ.subcategories:
                sys.stderr.write("'%s' has subcategories AND conferences!\n")

        # as for category-containing categories
        else:
            for subcat in categ.subcategories:
                if subcat not in index:
                    sys.stderr.write("'%s' is a child of '%s' but is not in the CategoryManager" % (subcat, cid))

        # check that the the category has a parent
        if categ.getOwner() == None and cid != '0':
            sys.stderr.write("'%s' has no owner!\n")

        # check that the contained id is the same as the indexation key
        if categ.getId() != cid:
            sys.stderr.write("'%s' indexed as '%s'\n" % (categ.getId(), cid))

    # now check that the event number totals are OK
    check_event_number_consistency(CategoryManager().getById('0'))
