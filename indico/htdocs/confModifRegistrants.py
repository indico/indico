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

import MaKaC.webinterface.rh.registrantsModif as registrantsModif



def index(req, **params):
    return registrantsModif.RHRegistrantListModif( req ).process( params )

def action(req, **params):
    return registrantsModif.RHRegistrantListModifAction( req ).process( params )

def newRegistrant(req, **params):
    return registrantsModif.RHRegistrantNewForm( req ).process( params )

def modification(req, **params):
    return registrantsModif.RHRegistrantModification( req ).process( params )

def dataModification(req, **params):
    return registrantsModif.RHRegistrantDataModification( req ).process( params )

def performDataModification(req, **params):
    return registrantsModif.RHRegistrantPerformDataModification( req ).process( params )

def getPDF(req, **params):
    return registrantsModif.RHRegistrantListPDF( req ).process( params )

def email(req, **params):
    return registrantsModif.RHRegistrantListEmail( req ).process( params )

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

def openMenu(req, **params):
    return registrantsModif.RHRegistrantListMenuOpen(req).process(params)

def closeMenu(req, **params):
    return registrantsModif.RHRegistrantListMenuClose(req).process(params)

def modifyStatuses(req, **params):
    return registrantsModif.RHRegistrantStatusesModify( req ).process( params )

def performModifyStatuses(req, **params):
    return registrantsModif.RHRegistrantStatusesPerformModify( req ).process( params )
