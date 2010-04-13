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
from MaKaC.webinterface.rh import subContribMod

def index(req, **params):
    return subContribMod.RHSubContributionModification( req ).process( params )

def data( req, **params ):
    return subContribMod.RHSubContributionData( req ).process( params )    


def modifData( req, **params ):
    return subContribMod.RHSubContributionModifData( req ).process( params )


def selectSpeakers(req, **params):
    return subContribMod.RHSubContributionSelectSpeakers( req ).process( params )
    

def addSpeakers(req, **params):
    return subContribMod.RHSubContributionAddSpeakers( req ).process( params )

def newSpeaker  (req, **params):
    return subContribMod.RHSubContribNewSpeaker( req ).process( params )

def removeSpeakers(req, **params):
    return subContribMod.RHSubContributionRemoveSpeakers( req ).process( params )
    
    
def addMaterial(req, **params):
    return subContribMod.RHSubContributionAddMaterial( req ).process( params )


def performAddMaterial(req, **params):
    return subContribMod.RHSubContributionPerformAddMaterial( req ).process( params )


def removeMaterials( req, **params ):
    return subContribMod.RHSubContributionRemoveMaterials( req ).process( params )

def materialsAdd(req, **params):
    return subContribMod.RHMaterialsAdd(req).process(params)

def modPresenter(req, **params):
    return subContribMod.RHEditPresenter( req ).process( params )

def materials(req, **params):
    return subContribMod.RHMaterials( req ).process( params )

def editReportNumber(req, **params):
    return subContribMod.RHSubContributionReportNumberEdit(req).process(params)

def performEditReportNumber(req, **params):
    return subContribMod.RHSubContributionReportNumberPerformEdit(req).process(params)
def removeReportNumber(req, **params):
    return subContribMod.RHSubContributionReportNumberRemove(req).process(params)
