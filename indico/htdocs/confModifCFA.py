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

import MaKaC.webinterface.rh.conferenceModif as conferenceModif


def index( req, **params ):
    return conferenceModif.RHConfModifCFA( req ).process( params )


def changeStatus( req, **params ):
    return conferenceModif.RHConfModifCFAStatus( req ).process( params )


def addType(req, **params):
    return conferenceModif.RHCFAAddType( req ).process( params )


def removeType(req, **params):
    return conferenceModif.RHCFARemoveType( req ).process( params )


def modifyData( req, **params ):
    return conferenceModif.RHCFADataModification( req ).process( params )


def performModifyData( req, **params ):
    return conferenceModif.RHCFAPerformDataModification( req ).process( params )

def addSubmitter( req, **params ):
    return conferenceModif.RHConfModifCFAAddSubmitter( req ).process( params )

def selectSubmitter( req, **params ):
    return conferenceModif.RHConfModifCFASelectSubmitter( req ).process( params )

def removeSubmitter( req, **params ):
    return conferenceModif.RHConfModifCFARemoveSubmitter( req ).process( params )

def notifTplNew(req,**params):
    return conferenceModif.RHCFANotifTplNew(req).process(params)


def notifTplRem(req,**params):
    return conferenceModif.RHCFANotifTplRem(req).process(params)


def notifTplEdit(req,**params):
    return conferenceModif.RHCFANotifTplEdit(req).process(params)


def notifTplDisplay(req,**params):
    return conferenceModif.RHCFANotifTplDisplay(req).process(params)


def notifTplPreview(req,**params):
    return conferenceModif.RHCFANotifTplPreview(req).process(params)


def notifTplCondNew(req,**params):
    return conferenceModif.RHNotifTplConditionNew(req).process(params)


def notifTplCondRem(req,**params):
    return conferenceModif.RHNotifTplConditionRem(req).process(params)


def notifTplUp(req,**params):
    return conferenceModif.RHCFANotifTplUp(req).process(params)

def notifTplDown(req,**params):
    return conferenceModif.RHCFANotifTplDown(req).process(params)

def abstractFields(req, **params):
    return conferenceModif.RHConfAbstractFields(req).process(params)

def addAbstractField(req, **params):
    return conferenceModif.RHConfAddAbstractField(req).process(params)

def editAbstractField(req, **params):
    return conferenceModif.RHConfEditAbstractField(req).process(params)

def performAddAbstractField(req, **params):
    return conferenceModif.RHConfPerformAddAbstractField(req).process(params)

def removeAbstractField(req, **params):
    return conferenceModif.RHConfRemoveAbstractField(req).process(params)

def absFieldUp(req, **params):
    return conferenceModif.RHConfMoveAbsFieldUp(req).process(params)

def absFieldDown(req, **params):
    return conferenceModif.RHConfMoveAbsFieldDown(req).process(params)

def preview(req, **params):
    return conferenceModif.RHConfModifCFAPreview(req).process(params)

def switchMultipleTracks(req, **params):
    return conferenceModif.RHConfModifCFASwitchMultipleTracks(req).process(params)

def makeTracksMandatory(req, **params):
    return conferenceModif.RHConfModifCFAMakeTracksMandatory(req).process(params)
