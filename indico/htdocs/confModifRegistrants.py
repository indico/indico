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

import MaKaC.webinterface.rh.registrantsModif as registrantsModif



def index(req, **params):
    return registrantsModif.RHRegistrantListModif( req ).process( params )

def action(req, **params):
    return registrantsModif.RHRegistrantListModifAction( req ).process( params )

def newRegistrant(req, **params):
    return registrantsModif.RHRegistrantNewForm( req ).process( params )

def modification(req, **params):
    return registrantsModif.RHRegistrantModification( req ).process( params )

def modifySessions(req, **params):
    return registrantsModif.RHRegistrantSessionModify( req ).process( params )

def modifyTransaction(req, **params):
    return registrantsModif.RHRegistrantTransactionModify( req ).process( params )

def peformModifyTransaction (req, **params):
    return registrantsModif.RHRegistrantTransactionPerformModify( req ).process( params )

def performModifySessions(req, **params):
    return registrantsModif.RHRegistrantSessionPerformModify( req ).process( params )

def modifyAccommodation(req, **params):
    return registrantsModif.RHRegistrantAccommodationModify( req ).process( params )

def performModifyAccommodation(req, **params):
    return registrantsModif.RHRegistrantAccommodationPerformModify( req ).process( params )

def modifySocialEvents(req, **params):
    return registrantsModif.RHRegistrantSocialEventsModify( req ).process( params )

def performModifySocialEvents(req, **params):
    return registrantsModif.RHRegistrantSocialEventsPerformModify( req ).process( params )

def modifyReasonParticipation(req, **params):
    return registrantsModif.RHRegistrantReasonParticipationModify( req ).process( params )

def performModifyReasonParticipation(req, **params):
    return registrantsModif.RHRegistrantReasonParticipationPerformModify( req ).process( params )

def modifyMiscInfo(req, **params):
    return registrantsModif.RHRegistrantMiscInfoModify( req ).process( params )

def performModifyMiscInfo(req, **params):
    return registrantsModif.RHRegistrantMiscInfoPerformModify( req ).process( params )

def remove(req, **params):
    return registrantsModif.RHRegistrantListRemove(req).process(params)

def modifyStatuses(req, **params):
    return registrantsModif.RHRegistrantStatusesModify( req ).process( params )

def performModifyStatuses(req, **params):
    return registrantsModif.RHRegistrantStatusesPerformModify( req ).process( params )

def getAttachedFile(req, **params):
    return registrantsModif.RHGetAttachedFile( req ).process(params)
