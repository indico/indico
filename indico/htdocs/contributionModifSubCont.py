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

from MaKaC.common.general import *

from MaKaC.webinterface.rh import contribMod

if DEVELOPMENT:
    contribMod = reload( contribMod )


def index(req, **params):
    return contribMod.RHContributionSC( req ).process( params )


def add(req, **params):
    return contribMod.RHContributionAddSC( req ).process( params )
    """
    p = pages.WPSubContributionCreation( req )
    params["postURL"] = "subContributionCreation.py/create"
    return p.display( params )
    """

def create(req, **params):
    return contribMod.RHContributionCreateSC( req ).process( params )
    """
    p = pages.WPSubContributionCreation( req )
    p.createSubContribution( params )
    return "done"
    """

def presenterSearch(req, **params):
    return contribMod.RHNewSubcontributionPresenterSearch(req).process(params)

def presenterNew(req, **params):
    return contribMod.RHNewSubcontributionPresenterNew(req).process(params)

def personAdd(req, **params):
    return contribMod.RHNewSubcontributionPersonAdd(req).process(params)


def actionSubContribs(req, **params):
    return contribMod.RHSubContribActions(req).process(params)

def delete(req, **params):
    return contribMod.RHContributionDeleteSC( req ).process( params )


def up(req, **params):
    return contribMod.RHContributionUpSC( req ).process( params )


def Down(req, **params):
    return contribMod.RHContributionDownSC( req ).process( params )
    

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

