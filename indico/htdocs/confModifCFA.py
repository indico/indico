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

import MaKaC.webinterface.rh.conferenceModif as conferenceModif


def index( req, **params ):
    return conferenceModif.RHConfModifCFA( req ).process( params )


def changeStatus( req, **params ):
    return conferenceModif.RHConfModifCFAStatus( req ).process( params )


def modifyData( req, **params ):
    return conferenceModif.RHCFADataModification( req ).process( params )


def performModifyData( req, **params ):
    return conferenceModif.RHCFAPerformDataModification( req ).process( params )

def abstractFields(req, **params):
    return conferenceModif.RHConfAbstractFields(req).process(params)

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

def switchAttachFiles(req, **params):
    return conferenceModif.RHConfModifCFASwitchAttachFiles(req).process(params)

def switchShowSelectSpeaker(req, **params):
    return conferenceModif.RHConfModifCFASwitchShowSelectAsSpeaker(req).process(params)

def switchSelectSpeakerMandatory(req, **params):
    return conferenceModif.RHConfModifCFASwitchSelectSpeakerMandatory(req).process(params)

def switchShowAttachedFiles(req, **params):
    return conferenceModif.RHConfModifCFASwitchShowAttachedFilesContribList(req).process(params)
