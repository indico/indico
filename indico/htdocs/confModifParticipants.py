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

def setup ( req, **params ):
    return conferenceModif.RHConfModifParticipantsSetup( req ).process( params )

def pendingParticipants( req, **params ):
    return conferenceModif.RHConfModifParticipantsPending( req ).process( params )

def declinedParticipants( req, **params ):
    return conferenceModif.RHConfModifParticipantsDeclined( req ).process( params )

def action( req, **params ):
    return conferenceModif.RHConfModifParticipantsAction( req ).process( params )

def statistics( req, **params ):
    return conferenceModif.RHConfModifParticipantsStatistics( req ).process( params )

def invitation( req, **params ):
    return conferenceDisplay.RHConfParticipantsInvitation( req ).process( params )

def refusal( req, **params ):
    return conferenceDisplay.RHConfParticipantsRefusal( req ).process( params )

