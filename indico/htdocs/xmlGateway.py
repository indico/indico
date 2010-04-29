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

from MaKaC.webinterface.rh import xmlGateway

def index( req, **params ):
    return xmlGateway.RHLoginStatus( req ).process( params )

def loginStatus(req, **params):
    return xmlGateway.RHLoginStatus( req ).process( params )

def signIn(req, **params):
    return xmlGateway.RHSignIn( req ).process( params )

def signOut(req, **params):
    return xmlGateway.RHSignOut( req ).process( params )

def addMaterialToConference(req, **params):
    return xmlGateway.RHAddMaterialToConference( req ).process( params )

def addMaterialToSession(req, **params):
    return xmlGateway.RHAddMaterialToSession( req ).process( params )

def addMaterialToContribution(req, **params):
    return xmlGateway.RHAddMaterialToContribution( req ).process( params )

def addMaterialToSubContribution(req, **params):
    return xmlGateway.RHAddMaterialToSubContribution( req ).process( params )

def createLecture( req, **params ):
    return xmlGateway.RHCreateLecture( req ).process( params )

def search( req, **params ):
    return xmlGateway.RHSearch( req ).process( params )

def getCategoryInfo( req, **params ):
    return xmlGateway.RHCategInfo( req ).process( params )

def webcastOnAir( req, **params ):
    return xmlGateway.RHWebcastOnAir( req ).process( params )

def webcastForthcomingEvents( req, **params ):
    return xmlGateway.RHWebcastForthcomingEvents( req ).process( params )

def getStatsRoomBooking( req, **params ):
    return xmlGateway.RHStatsRoomBooking( req ).process( params )

def getStatsIndico( req, **params ):
    return xmlGateway.RHStatsIndico( req ).process( params )
