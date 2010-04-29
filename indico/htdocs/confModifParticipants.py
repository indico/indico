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
from MaKaC.webinterface.rh import conferenceDisplay


def index( req, **params ):
    return conferenceModif.RHConfModifParticipants( req ).process( params )

def obligatory ( req, **params ):
    return conferenceModif.RHConfModifParticipantsObligatory( req ).process( params )

def display ( req, **params ):
    return conferenceModif.RHConfModifParticipantsDisplay( req ).process( params )

def addedInfo ( req, **params ):
    return conferenceModif.RHConfModifParticipantsAddedInfo( req ).process( params )
    
def allowForApplying( req, **params ):
    return conferenceModif.RHConfModifParticipantsAllowForApplying( req ).process( params )

def toggleAutoAccept( req, **params ):
    return conferenceModif.RHConfModifParticipantsToggleAutoAccept( req ).process( params )

def pendingParticipants( req, **params ):
    return conferenceModif.RHConfModifParticipantsPending( req ).process( params )

def action( req, **params ):
    return conferenceModif.RHConfModifParticipantsAction( req ).process( params )
    
def statistics( req, **params ):
    return conferenceModif.RHConfModifParticipantsStatistics( req ).process( params )
    
def selectToAdd( req, **params ):
    return conferenceModif.RHConfModifParticipantsSelectToAdd( req ).process( params )

def addSelected( req, **params ):
    return conferenceModif.RHConfModifParticipantsAddSelected( req ).process( params )
    
def newToAdd( req, **params ):
    return conferenceModif.RHConfModifParticipantsNewToAdd( req ).process( params )
    
def addNew( req, **params ):
    return conferenceModif.RHConfModifParticipantsAddNew( req ).process( params )
    
def selectToInvite( req, **params ):
    return conferenceModif.RHConfModifParticipantsSelectToInvite( req ).process( params )
    
def inviteSelected( req, **params ):
    return conferenceModif.RHConfModifParticipantsInviteSelected( req ).process( params )
    
def newToInvite( req, **params ):
    return conferenceModif.RHConfModifParticipantsNewToInvite( req ).process( params )
    
def inviteNew( req, **params ):
    return conferenceModif.RHConfModifParticipantsInviteNew( req ).process( params )
    
def details( req, **params ):
    return conferenceModif.RHConfModifParticipantsDetails( req ).process( params )
    
def edit( req, **params ):
    return conferenceModif.RHConfModifParticipantsEdit( req ).process( params )

def pendingAction( req, **params ):
    return conferenceModif.RHConfModifParticipantsPendingAction( req ).process( params )
            
def pendingDetails( req, **params ):
    return conferenceModif.RHConfModifParticipantsPendingDetails( req ).process( params )

def pendingEdit( req, **params ):
    return conferenceModif.RHConfModifParticipantsPendingEdit( req ).process( params )
    
def newPending( req, **params ):
    return conferenceDisplay.RHConfParticipantsNewPending( req ).process( params )
    
def addPending( req, **params ):
    return conferenceDisplay.RHConfParticipantsAddPending( req ).process( params )
    
def invitation( req, **params ):
    return conferenceDisplay.RHConfParticipantsInvitation( req ).process( params )
    
def refusal( req, **params ):
    return conferenceDisplay.RHConfParticipantsRefusal( req ).process( params )
    
def sendEmail( req, **params ):
    return conferenceModif.RHConfModifParticipantsSendEmail( req ).process( params )
    