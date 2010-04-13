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

from MaKaC.webinterface.rh import conferenceDisplay
from MaKaC.webinterface.rh import authorDisplay
from MaKaC.webinterface.rh import registrantsModif
from MaKaC.webinterface.rh import conferenceModif


def index(req, **params):
    return conferenceDisplay.RHConferenceEmail( req ).process( params )

def send (req, **params):
    return conferenceDisplay.RHConferenceSendEmail( req ).process( params )


def sendreg (req, **params):
    return registrantsModif.RHRegistrantSendEmail( req ).process( params )
    
def sendconvener (req, **params):
    return conferenceModif.RHConvenerSendEmail( req ).process( params )

def sendcontribparticipants(req, **params):
    return conferenceModif.RHContribParticipantsSendEmail( req ).process( params )
