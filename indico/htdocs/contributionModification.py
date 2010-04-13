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

def newPrimAuthor(req, **params):
    return contribMod.RHNewPrimaryAuthor( req ).process( params )

def searchPrimAuthor(req, **params):
    return contribMod.RHSearchPrimaryAuthor( req ).process( params )

def searchAddPrimAuthor(req, **params):
    return contribMod.RHSearchAddPrimaryAuthor( req ).process( params )

def searchCoAuthor(req, **params):
    return contribMod.RHSearchCoAuthor( req ).process( params )

def searchAddCoAuthor(req, **params):
    return contribMod.RHSearchAddCoAuthor( req ).process( params )

def remPrimAuthors(req, **params):
    return contribMod.RHRemPrimaryAuthors( req ).process( params )

def modPrimAuthor(req, **params):
    return contribMod.RHEditPrimaryAuthor( req ).process( params )

def newCoAuthor(req, **params):
    return contribMod.RHNewCoAuthor( req ).process( params )

def remCoAuthors(req, **params):
    return contribMod.RHRemCoAuthors( req ).process( params )

def modCoAuthor(req, **params):
    return contribMod.RHEditCoAuthor( req ).process( params )

def addMaterial(req, **params):
    return contribMod.RHContributionAddMaterial( req ).process( params )

def performAddMaterial(req, **params):
    return contribMod.RHContributionPerformAddMaterial( req ).process( params )

def schedule(req, **params):
    return contribMod.RHContributionSchedule( req ).process( params )

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
    

def addSpk( req, **params ):
    return contribMod.RHAddSpeakers( req ).process( params )


def remSpk( req, **params ):
    return contribMod.RHRemSpeakers( req ).process( params )

def searchSpk( req, **params ):
    return contribMod.RHSearchSpeakers( req ).process( params )

def searchAddSpk(req, **params):
    return contribMod.RHSearchAddSpeakers( req ).process( params )

def setTrack( req, **params ):
    return contribMod.RHSetTrack( req ).process( params )


def setSession( req, **params ):
    return contribMod.RHSetSession( req ).process( params )

def withdraw(req, **params):
    return contribMod.RHWithdraw( req ).process( params )

def primAuthUp(req, **params):
    return contribMod.RHPrimAuthUp( req ).process( params )

def primAuthDown(req, **params):
    return contribMod.RHPrimAuthDown( req ).process( params )

def coAuthUp(req, **params):
    return contribMod.RHCoAuthUp( req ).process( params )

def coAuthDown(req, **params):
    return contribMod.RHCoAuthDown( req ).process( params )

def primaryAuthorAction(req, **params):
    return contribMod.RHPrimaryAuthorsActions( req ).process( params )

def coAuthorAction(req, **params):
    return contribMod.RHCoAuthorsActions( req ).process( params )

def newSpeaker(req, **params):
    return contribMod.RHNewSpeaker( req ).process( params )

def modSpeaker(req, **params):
    return contribMod.RHEditSpeaker( req ).process( params )

def materials(req, **params):
    return contribMod.RHMaterials( req ).process( params )

def editReportNumber(req, **params):
    return contribMod.RHContributionReportNumberEdit(req).process(params)

def performEditReportNumber(req, **params):
    return contribMod.RHContributionReportNumberPerformEdit(req).process(params)

def removeReportNumber(req, **params):
    return contribMod.RHContributionReportNumberRemove(req).process(params)
