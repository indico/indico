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

"""Contains tests regarding some scenarios related to contribution list display.
"""
import unittest
import os

from datetime import datetime,timedelta
from pytz import timezone


class TestContributionList(unittest.TestCase):
    """Tests the contribution list functions
    """

    def setUp( self ):
        from MaKaC.user import Avatar
        a = Avatar()
        a.setId("creator")
        from MaKaC.conference import Conference
        self._conf=Conference(a)
        self._conf.setTimezone('UTC')
        self._conf.setDates(datetime(2000,1,1,tzinfo=timezone('UTC')),datetime(2020,1,1,tzinfo=timezone('UTC')))

    def testSorting( self ):
        from MaKaC.conference import Contribution, ContributionType, Session, Track
        from MaKaC.webinterface.common import contribFilters
        from MaKaC.common.filters import SimpleFilter
        contrib1 = Contribution()
        contrib2 = Contribution()
        contrib3 = Contribution()
        self._conf.addContribution( contrib1 )
        self._conf.addContribution( contrib2 )
        self._conf.addContribution( contrib3 )
        # Sorting by ID
        sortingCrit = contribFilters.SortingCriteria( ["number"] )
        f = SimpleFilter( None, sortingCrit )
        contribList = f.apply(self._conf.getContributionList())
        self.assert_( len(contribList) == 3 )
        self.assert_( contribList[0] == contrib1 )
        self.assert_( contribList[1] == contrib2 )
        self.assert_( contribList[2] == contrib3 )
        #Sorting by Date
        contrib1.setStartDate(datetime(2004, 5, 1, 10, 30,tzinfo=timezone('UTC')))
        contrib2.setStartDate(datetime(2003, 5, 1, 10, 30,tzinfo=timezone('UTC')))
        sortingCrit = contribFilters.SortingCriteria( ["date"] )
        f = SimpleFilter( None, sortingCrit )
        contribList = f.apply(self._conf.getContributionList())
        self.assert_( len(contribList) == 3 )
        self.assert_( contribList[0] == contrib2 )
        self.assert_( contribList[1] == contrib1 )
        self.assert_( contribList[2] == contrib3 )
        # Sorting by Contribution Type
        contribType1 = ContributionType("oral presentation", "no description", self._conf)
        contribType2 = ContributionType("poster", "no description", self._conf)
        contrib1.setType(contribType1)
        contrib2.setType(contribType2)
        sortingCrit = contribFilters.SortingCriteria( ["type"] )
        f = SimpleFilter( None, sortingCrit )
        contribList = f.apply(self._conf.getContributionList())
        self.assert_( len(contribList) == 3 )
        self.assert_( contribList[0] == contrib1 )
        self.assert_( contribList[1] == contrib2 )
        self.assert_( contribList[2] == contrib3 )
        # Sorting by Session
        session1 = Session()
        self._conf.addSession(session1)
        session2 = Session()
        self._conf.addSession(session2)
        contrib1.setSession(session1)
        contrib2.setSession(session2)
        sortingCrit = contribFilters.SortingCriteria( ["session"] )
        f = SimpleFilter( None, sortingCrit )
        contribList = f.apply(self._conf.getContributionList())
        self.assert_( len(contribList) == 3 )
        self.assert_(contrib1 in contribList)
        self.assert_(contrib2 in contribList)
        self.assert_(contrib3 in contribList)
        # Sorting by Track
        track1 = Track()
        track1.setTitle("3")
        track1.setConference(self._conf)
        track2 = Track()
        track2.setTitle("1")
        track2.setConference(self._conf)
        contrib1.setTrack(track1)
        contrib2.setTrack(track2)
        sortingCrit = contribFilters.SortingCriteria( ["track"] )
        f = SimpleFilter( None, sortingCrit )
        contribList = f.apply(self._conf.getContributionList())
        self.assert_( len(contribList) == 3 )
        self.assert_( contribList[0] == contrib2 )
        self.assert_( contribList[1] == contrib1 )
        self.assert_( contribList[2] == contrib3 )
        


def testsuite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite(TestContributionList) )
    return suite

