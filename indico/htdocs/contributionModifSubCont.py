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

def actionSubContribs(req, **params):
    return contribMod.RHSubContribActions(req).process(params)

def delete(req, **params):
    return contribMod.RHContributionDeleteSC( req ).process( params )


def up(req, **params):
    return contribMod.RHContributionUpSC( req ).process( params )


def Down(req, **params):
    return contribMod.RHContributionDownSC( req ).process( params )

def setVisibility( req, **params ):
    return contribMod.RHContributionSetVisibility( req ).process( params )
