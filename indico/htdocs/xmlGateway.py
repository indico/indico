# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

from MaKaC.webinterface.rh import xmlGateway

def index( req, **params ):
    return xmlGateway.RHLoginStatus( req ).process( params )

def loginStatus(req, **params):
    return xmlGateway.RHLoginStatus( req ).process( params )

def signIn(req, **params):
    return xmlGateway.RHSignIn( req ).process( params )

def signOut(req, **params):
    return xmlGateway.RHSignOut( req ).process( params )

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
