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

from MaKaC.webinterface.rh import contribMod


def index(req, **params):
    return contribMod.RHContributionAC( req ).process( params )

def selectManagers( req, **params ):
    return contribMod.RHContributionSelectManagers( req ).process( params )

def addManagers( req, **params ):
    return contribMod.RHContributionAddManagers( req ).process( params )

def removeManagers( req, **params ):
    return contribMod.RHContributionRemoveManagers( req ).process( params )

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

def removeSubmitters( req, **params ):
    return contribMod.RHSubmittersRem( req ).process( params )

def selectSubmitters( req, **params ):
    return contribMod.RHSubmittersSel( req ).process( params )

def addSubmitters( req, **params ):
    return contribMod.RHSubmittersAdd( req ).process( params )

