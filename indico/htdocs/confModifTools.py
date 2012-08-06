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

from MaKaC.webinterface.rh import conferenceModif


def index( req, **params ):
    return conferenceModif.RHConfModifTools( req ).process( params )

def delete( req, **params ):
    return conferenceModif.RHConfDeletion( req ).process( params )

def clone( req, **params ):
    return conferenceModif.RHConfClone( req ).process( params )

def performCloning( req, **params ):
    return conferenceModif.RHConfPerformCloning(req).process(params)

def allSessionsConveners( req, **params ):
    return conferenceModif.RHConfAllSessionsConveners( req ).process( params )

def allSessionsConvenersAction( req, **params ):
    return conferenceModif.RHConfAllSessionsConvenersAction( req ).process( params )

def displayAlarm( req, **params ):
    return conferenceModif.RHConfDisplayAlarm( req ).process( params )

def addAlarm( req, **params ):
    return conferenceModif.RHConfAddAlarm( req ).process( params )

def saveAlarm( req, **params ):
    return conferenceModif.RHConfSaveAlarm( req ).process( params )

def sendAlarmNow( req, **params ):
    return conferenceModif.RHConfSendAlarmNow( req ).process( params )

def deleteAlarm( req, **params ):
    return conferenceModif.RHConfDeleteAlarm( req ).process( params )

def modifyAlarm( req, **params ):
    return conferenceModif.RHConfModifyAlarm( req ).process( params )

def matPkg( req, **params ):
    return conferenceModif.RHFullMaterialPackage( req ).process( params )

def performMatPkg( req, **params ):
    return conferenceModif.RHFullMaterialPackagePerform( req ).process( params )

def badgePrinting (req, **params):
    return conferenceModif.RHConfBadgePrinting(req).process(params)

def badgeDesign (req, **params):
    return conferenceModif.RHConfBadgeDesign(req).process(params)

def badgePrintingPDF (req, **params):
    return conferenceModif.RHConfBadgePrintingPDF(req).process(params)

def badgeSaveBackground (req, **params):
    return conferenceModif.RHConfBadgeSaveTempBackground(req).process(params)

def badgeGetBackground (req, **params):
    return conferenceModif.RHConfBadgeGetBackground(req).process(params)

def posterPrinting (req, **params):
    return conferenceModif.RHConfPosterPrinting(req).process(params)

def posterPrintingPDF (req, **params):
    return conferenceModif.RHConfPosterPrintingPDF(req).process(params)

def posterDesign (req, **params):
    return conferenceModif.RHConfPosterDesign(req).process(params)

def posterSaveBackground (req, **params):
    return conferenceModif.RHConfPosterSaveTempBackground(req).process(params)

def posterGetBackground (req, **params):
    return conferenceModif.RHConfPosterGetBackground(req).process(params)
