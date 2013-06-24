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

from MaKaC.webinterface.rh import sessionModif


def index(req, **params):
    return sessionModif.RHSessionModification( req ).process( params )

def modify( req, **params ):
    return sessionModif.RHSessionDataModification( req ).process( params )

def close( req, **params ):
    return sessionModif.RHSessionClose( req ).process( params )

def open( req, **params ):
    return sessionModif.RHSessionOpen( req ).process( params )

def materialsAdd(req, **params):
    return sessionModif.RHMaterialsAdd(req).process(params)

def addContribs( req, **params ):
    return sessionModif.RHAddContribs( req ).process( params )

def contribList( req, **params ):
    return sessionModif.RHContribList( req ).process( params )

def editContrib( req, **params ):
    return sessionModif.RHContribListEditContrib( req ).process( params )

def contribAction( req, **params ):
    return sessionModif.RHContribsActions( req ).process( params )

def contribQuickAccess( req, **params ):
    return sessionModif.RHContribQuickAccess(req).process(params)

def participantList( req, **params ):
    return sessionModif.RHContribsParticipantList(req).process(params)

def contribsToPDF( req, **params ):
    return sessionModif.RHContribsToPDF(req).process(params)

def materials(req, **params):
    return sessionModif.RHMaterials( req ).process( params )
