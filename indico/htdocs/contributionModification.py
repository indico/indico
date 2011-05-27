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
    return contribMod.RHContributionModification( req ).process( params )

def browseMaterial(req, **params):
    return contribMod.RHContribModifMaterialBrowse( req ).process( params )

def addMaterial(req, **params):
    return contribMod.RHContributionAddMaterial( req ).process( params )

def performAddMaterial(req, **params):
    return contribMod.RHContributionPerformAddMaterial( req ).process( params )

def materialsAdd(req, **params):
    return contribMod.RHMaterialsAdd(req).process(params)

def removeMaterials( req, **params ):
    return contribMod.RHContributionRemoveMaterials( req ).process( params )


def move( req, **params ):
    return contribMod.RHContributionMove( req ).process( params )


def performMove( req, **params ):
    return contribMod.RHContributionPerformMove( req ).process( params )


def data( req, **params ):
    return contribMod.RHContributionData( req ).process( params )


def xml( req, **params ):
    return contribMod.RHContributionToXML( req ).process( params )


def pdf( req, **params ):
    return contribMod.RHContributionToPDF( req ).process( params )


def modifData( req, **params ):
    return contribMod.RHContributionModifData( req ).process( params )


def setTrack( req, **params ):
    return contribMod.RHSetTrack( req ).process( params )


def setSession( req, **params ):
    return contribMod.RHSetSession( req ).process( params )

def withdraw(req, **params):
    return contribMod.RHWithdraw( req ).process( params )

def materials(req, **params):
    return contribMod.RHMaterials( req ).process( params )

def editReportNumber(req, **params):
    return contribMod.RHContributionReportNumberEdit(req).process(params)

def performEditReportNumber(req, **params):
    return contribMod.RHContributionReportNumberPerformEdit(req).process(params)

def removeReportNumber(req, **params):
    return contribMod.RHContributionReportNumberRemove(req).process(params)
