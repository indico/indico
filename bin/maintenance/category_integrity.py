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
This simple script checks whether the `_numConferences` attribute is consistent for
every category, and fixs them otherwise.

It can be added as a periodic cronjob.
"""

import sys

from MaKaC.common import DBMgr
from MaKaC.conference import CategoryManager



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


def check_event_number_leaves(categ, dbi):
    expected = len(categ.conferences)
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

    index = CategoryManager()._getIdx()

    for cid, categ in index.iteritems():
        # conferece-containing categories
        if categ.conferences:

            # since we're here check consistency of TreeSet
            categ.conferences._check()

            # check event numbers
            check_event_number_leaves(categ, dbi)

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
