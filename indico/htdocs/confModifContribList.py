# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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
    return conferenceModif.RHContributionList( req ).process( params )

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
