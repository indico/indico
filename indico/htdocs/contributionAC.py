# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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

from MaKaC.webinterface.rh import contribMod


def index(req, **params):
    return contribMod.RHContributionAC( req ).process( params )

def setVisibility( req, **params ):
    return contribMod.RHContributionSetVisibility( req ).process( params )

def selectAllowedToAccess( req, **params ):
    return contribMod.RHContributionSelectAllowed( req ).process( params )

def addAllowedToAccess( req, **params ):
    return contribMod.RHContributionAddAllowed( req ).process( params )

def removeAllowedToAccess( req, **params ):
    return contribMod.RHContributionRemoveAllowed( req ).process( params )

def addDomains( req, **params ):
    return contribMod.RHContributionAddDomains( req ).process( params )

def removeDomains( req, **params ):
    return contribMod.RHContributionRemoveDomains( req ).process( params )
