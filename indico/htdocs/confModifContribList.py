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

from MaKaC.webinterface.rh import conferenceModif


def index( req, **params ):
    return conferenceModif.RHContributionList( req ).process( params )

def openMenu( req, **params ):
    return conferenceModif.RHContributionListOpenMenu( req ).process( params )

def closeMenu( req, **params ):
    return conferenceModif.RHContributionListCloseMenu( req ).process( params )

def addContribution( req, **params ):
    return conferenceModif.RHConfAddContribution(req).process(params)

def performAddContribution( req, **params ):
    return conferenceModif.RHConfPerformAddContribution(req).process(params)

def performAddContributionM( req, **params ):
    return conferenceModif.RHMConfPerformAddContribution(req).process(params)

def contribQuickAccess(req,**params):
    return conferenceModif.RHContribQuickAccess(req).process(params)

def contribsActions( req, **params ):
    return conferenceModif.RHContribsActions( req ).process( params )

def contribsToPDFMenu( req, **params ):
    return conferenceModif.RHContribsToPDFMenu( req ).process( params )

def contribsToPDF( req, **params ):
    return conferenceModif.RHContribsToPDF( req ).process( params )

def participantList( req, **params ):
    return conferenceModif.RHContribsParticipantList( req ).process( params )

def moveToSession( req, **params ):
    return conferenceModif.RHMoveContribsToSession( req ).process( params )

def matPkg( req, **params ):
    return conferenceModif.RHMaterialPackage( req ).process( params )

def proceedings( req, **params ):
    return conferenceModif.RHProceedings( req ).process( params )

