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

from MaKaC.webinterface.rh import sessionModif


def index( req, **params ):
    return sessionModif.RHSessionModifAC( req ).process( params )

def setVisibility( req, **params ):
    return sessionModif.RHSessionSetVisibility( req ).process( params )

def selectAllowed( req, **params ):
    return sessionModif.RHSessionSelectAllowed( req ).process( params )

def addAllowed( req, **params ):
    return sessionModif.RHSessionAddAllowed( req ).process( params )

def removeAllowed( req, **params ):
    return sessionModif.RHSessionRemoveAllowed( req ).process( params )

def addDomains( req, **params ):
    return sessionModif.RHSessionAddDomains( req ).process( params )

def removeDomains( req, **params ):
    return sessionModif.RHSessionRemoveDomains( req ).process( params )

def selectManagers( req, **params ):
    return sessionModif.RHSessionSelectManagers( req ).process( params )

def addManagers( req, **params ):
    return sessionModif.RHSessionAddManagers( req ).process( params )

def removeManagers( req, **params ):
    return sessionModif.RHSessionRemoveManagers( req ).process( params )

def selectCoordinators( req, **params ):
    return sessionModif.RHCoordinatorsSel( req ).process( params )

def addCoordinators( req, **params ):
    return sessionModif.RHCoordinatorsAdd( req ).process( params )

def remCoordinators( req, **params ):
    return sessionModif.RHCoordinatorsRem( req ).process( params )
