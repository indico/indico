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

"""Contains tests about some typical "scientific programme" scenarios.
"""

import unittest

class TestTCIndex( unittest.TestCase ):
    """Makes sure the track coordinators index is working properly as standalone
        component
    """

    def setUp( self ):
        #Build an index
        from MaKaC.conference import TCIndex
        self._idx = TCIndex()

    def tearDown( self ):
        pass

    def testSimpleIndexing( self ):
        #adding a simple object to the index
        from MaKaC.user import Avatar
        av = Avatar()
        av.setId( "1" ) #the index needs the avatar to be uniquely identified
        from MaKaC.conference import Track
        t = Track()
        t.setId( "1" )
        self._idx.indexCoordinator( av , t )
        self.assert_( len(self._idx.getTracks( av )) == 1 )
        self.assert_( t in self._idx.getTracks( av ) )
    
    def testIndexingSeveralCoordinators( self ):
        #adding 2 coordinators for the same track
        from MaKaC.user import Avatar
        av1 = Avatar()
        av1.setId( "1" ) #the index needs the avatar to be uniquely identified
        av2 = Avatar()
        av2.setId( "2" ) #the index needs the avatar to be uniquely identified
        from MaKaC.conference import Track
        t = Track()
        t.setId( "1" )
        self._idx.indexCoordinator( av1 , t )
        self._idx.indexCoordinator( av2 , t )
        self.assert_( t in self._idx.getTracks( av1 ) )
        self.assert_( t in self._idx.getTracks( av2 ) )
    
    def testIndexingSeveralTracks( self ):
        #adding 1 coordinator for 2 tracks
        from MaKaC.user import Avatar
        av1 = Avatar()
        av1.setId( "1" ) #the index needs the avatar to be uniquely identified
        from MaKaC.conference import Track
        t1 = Track()
        t1.setId( "1" )
        t2 = Track()
        t2.setId( "2" )
        self._idx.indexCoordinator( av1 , t1 )
        self._idx.indexCoordinator( av1 , t2 )
        self.assert_( t1 in self._idx.getTracks( av1 ) )
        self.assert_( t2 in self._idx.getTracks( av1 ) )

    def testSimpleUnidexing( self ):
        #check that unindexing works properly
        from MaKaC.user import Avatar
        av = Avatar()
        av.setId( "1" ) #the index needs the avatar to be uniquely identified
        from MaKaC.conference import Track
        t = Track()
        t.setId( "1" )
        self._idx.indexCoordinator( av , t )
        self._idx.unindexCoordinator( av, t )
        self.assert_( len(self._idx.getTracks( av )) == 0 )
    
    def testUnindexingSeveralCoordinators( self ):
        from MaKaC.user import Avatar
        av1 = Avatar()
        av1.setId( "1" ) #the index needs the avatar to be uniquely identified
        av2 = Avatar()
        av2.setId( "2" ) #the index needs the avatar to be uniquely identified
        from MaKaC.conference import Track
        t1 = Track()
        t1.setId( "1" )
        self._idx.indexCoordinator( av1 , t1 )
        self._idx.indexCoordinator( av2 , t1 )
        self._idx.unindexCoordinator( av1, t1 )
        self.assert_( t1 not in self._idx.getTracks( av1 ) )
        self.assert_( t1 in self._idx.getTracks( av2 ) )
    
    def testUnindexingSeveralTracks( self ):
        from MaKaC.user import Avatar
        av1 = Avatar()
        av1.setId( "1" ) #the index needs the avatar to be uniquely identified
        from MaKaC.conference import Track
        t1 = Track()
        t1.setId( "1" )
        t2 = Track()
        t2.setId( "2" )
        self._idx.indexCoordinator( av1 , t1 )
        self._idx.indexCoordinator( av1 , t2 )
        self._idx.unindexCoordinator( av1, t1 )
        self.assert_( t1 not in self._idx.getTracks( av1 ) )
        self.assert_( t2 in self._idx.getTracks( av1 ) )


class TestAddTrackCoordinator( unittest.TestCase ):
    """Tests different scenarios of the Define Track Coord use case.
    """
    
    def setUp( self ):
        from MaKaC.user import Avatar
        cr = Avatar()
        cr.setId( "creator" )
        from MaKaC.conference import Conference, Track
        self._conf = Conference( cr )
        self._track1 = Track()
        self._track1.setId( "1" )
        self._conf.addTrack( self._track1 )
        

    def tearDown( self ):
        pass

    def testAddTC( self ):
        from MaKaC.user import Avatar
        tc1 = Avatar()
        tc1.setId( "tc1" )
        self._track1.addCoordinator( tc1 )
        self.assert_( len(self._track1.getCoordinatorList()) == 1 )
        self.assert_( tc1 in self._track1.getCoordinatorList() )
        self.assert_( self._track1 in self._conf.getCoordinatedTracks( tc1 ) )


class TestRemoveTrackCoordinator( unittest.TestCase ):
    """Tests different scenarios of the Remove Track Coord use case.
    """
    
    def setUp( self ):
        from MaKaC.user import Avatar
        cr = Avatar()
        cr.setId( "creator" )
        from MaKaC.conference import Conference, Track
        self._conf = Conference( cr )
        self._track1 = Track()
        self._track1.setId( "1" )
        self._conf.addTrack( self._track1 )
        
    def tearDown( self ):
        pass

    def testRemoveTC( self ):
        from MaKaC.user import Avatar
        tc1 = Avatar()
        tc1.setId( "tc1" )
        tc2 = Avatar()
        tc2.setId( "tc2" )
        self._track1.addCoordinator( tc1 )
        self._track1.addCoordinator( tc2 )
        self._track1.removeCoordinator( tc1 )
        self.assert_( tc1 not in self._track1.getCoordinatorList() )
        self.assert_( tc2 in self._track1.getCoordinatorList() )
        self.assert_( self._track1 not in self._conf.getCoordinatedTracks( tc1 ) )
        self.assert_( self._track1 in self._conf.getCoordinatedTracks( tc2 ) )


class TestContributionInclusion( unittest.TestCase ):
    
    def setUp( self ):
        from MaKaC.user import Avatar
        cr = Avatar()
        cr.setId( "creator" )
        from MaKaC.conference import Conference, Track
        self._conf = Conference( cr )
        self._track1 = Track()
        self._track1.setId( "1" )
        self._conf.addTrack( self._track1 )

    def test( self ):
        from MaKaC.conference import Contribution
        contrib1 = Contribution()
        self._conf.addContribution( contrib1 )
        self._track1.addContribution( contrib1 )
        self.assert_( self._track1.hasContribution( contrib1 ) )
        self.assert_( contrib1.getTrack() == track1 )
        self._track1.removeContribution( contrib1 )
        self.assert_( not self._track1.hasContribution( contrib1 ) )
        self.assert_( contrib1.getTrack() == None )

def testsuite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite(TestTCIndex) )
    suite.addTest( unittest.makeSuite(TestAddTrackCoordinator) )
    suite.addTest( unittest.makeSuite(TestRemoveTrackCoordinator) )
    return suite


