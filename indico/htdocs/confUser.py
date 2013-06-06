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


from MaKaC.webinterface.rh import conferenceDisplay


def index(req, **params):
    return conferenceDisplay.RHConfUserCreation( req ).process( params )

def userExists(req, **params ):
    return conferenceDisplay.RHConfUserExistWithIdentity( req ).process( params )

def modify(req, **params):
    return users.RHUserModification( req ).process( params )

#def update(req, **params ):
#    return users.RHUserPerformModification( req ).process( params )

def active(req, **params ):
    return users.RHUserActive( req ).process( params )

def created(req, **params ):
    return conferenceDisplay.RHConfUserCreated( req ).process( params )
