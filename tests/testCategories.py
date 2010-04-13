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
"""
import unittest

from MaKaC import conference
from MaKaC import user


class TestNumConferences( unittest.TestCase ):
    """Verifies the correct management of the number of conferences counter 
        kept by the categories
    """

    def testBasicAddAndRemoveConferences(self):
        #creation of basic category structure over which perform the tests
        croot=conference.Category()
        c1=conference.Category()
        croot._addSubCategory(c1)
        c2=conference.Category()
        croot._addSubCategory(c2)
        c1_1=conference.Category()
        c1._addSubCategory(c1_1)
        #checks adding a conference increases the conference number of the 
        #   involved categories
        creator=user.Avatar()
        conf1=conference.Conference(creator)
        conf1.setId("0")
        c1_1._addConference(conf1)
        self.assert_(c1_1.getNumConferences()==1)
        self.assert_(c1.getNumConferences()==1)
        self.assert_(c2.getNumConferences()==0)
        self.assert_(croot.getNumConferences()==1)
        conf2=conference.Conference(creator)
        conf2.setId("1")
        c2._addConference(conf2)
        self.assert_(c1_1.getNumConferences()==1)
        self.assert_(c1.getNumConferences()==1)
        self.assert_(c2.getNumConferences()==1)
        self.assert_(croot.getNumConferences()==2)
        c1_1.removeConference(conf1)
        self.assert_(c1_1.getNumConferences()==0)
        self.assert_(c1.getNumConferences()==0)
        self.assert_(c2.getNumConferences()==1)
        self.assert_(croot.getNumConferences()==1)
        c2.removeConference(conf2)
        self.assert_(c1_1.getNumConferences()==0)
        self.assert_(c1.getNumConferences()==0)
        self.assert_(c2.getNumConferences()==0)
        self.assert_(croot.getNumConferences()==0)

    def testAddAndRemoveSubCategories(self):
        #checks that the conference counter works fine when adding a new
        #   sub-category
        croot=conference.Category()
        c1=conference.Category()
        c2=conference.Category()
        croot._addSubCategory(c2)
        creator=user.Avatar()
        conf0=conference.Conference(creator)
        conf0.setId("0")
        conf1=conference.Conference(creator)
        conf1.setId("1")
        c1._addConference(conf0)
        c1._addConference(conf1)
        self.assert_(croot.getNumConferences()==0)
        self.assert_(c1.getNumConferences()==2)
        self.assert_(c2.getNumConferences()==0)
        croot._addSubCategory(c1)
        self.assert_(croot.getNumConferences()==2)
        self.assert_(c1.getNumConferences()==2)
        self.assert_(c2.getNumConferences()==0)
        c1_1=conference.Category()
        c1._addSubCategory(c1_1)
        self.assert_(croot.getNumConferences()==2)
        self.assert_(c1.getNumConferences()==2)
        self.assert_(c1_1.getNumConferences()==2)
        self.assert_(c2.getNumConferences()==0)
        c1_1.move(c2)
        self.assert_(croot.getNumConferences()==2)
        self.assert_(c1.getNumConferences()==0)
        self.assert_(c1_1.getNumConferences()==2)
        self.assert_(c2.getNumConferences()==2)
        croot._removeSubCategory(c1)
        self.assert_(croot.getNumConferences()==2)
        self.assert_(c1.getNumConferences()==0)
        self.assert_(c1_1.getNumConferences()==2)
        self.assert_(c2.getNumConferences()==2)
        c2._removeSubCategory(c1_1)
        self.assert_(croot.getNumConferences()==0)
        self.assert_(c1.getNumConferences()==0)
        self.assert_(c1_1.getNumConferences()==2)
        self.assert_(c2.getNumConferences()==0)


def testsuite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite(TestNumConferences) )
    return suite

