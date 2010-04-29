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

from MaKaC.common.general import *

from MaKaC.webinterface.rh import conferenceModif

if DEVELOPMENT:
    conferenceModif = reload( conferenceModif )


def index( req, **params ):
    return conferenceModif.RHConfModifAC( req ).process( params )

def setVisibility(req, **params):
    return conferenceModif.RHConfSetVisibility( req ).process( params )

def setAccessKey(req, **params):
    return conferenceModif.RHConfSetAccessKey( req ).process( params )

def setModifKey(req, **params):
    return conferenceModif.RHConfSetModifKey( req ).process( params )

def selectAllowed( req, **params ):
    return conferenceModif.RHConfSelectAllowed( req ).process( params )

def addAllowed( req, **params ):
    return conferenceModif.RHConfAddAllowed( req ).process( params )

def removeAllowed(req, **params):
    return conferenceModif.RHConfRemoveAllowed( req ).process( params )

def addDomains( req, **params ):
    return conferenceModif.RHConfAddDomains( req ).process( params )

def removeDomains( req, **params ):
    return conferenceModif.RHConfRemoveDomains( req ).process( params )

def selectManagers( req, **params ):
    return conferenceModif.RHConfSelectManagers( req ).process( params )

def addManagers( req, **params ):
    return conferenceModif.RHConfAddManagers( req ).process( params )

def removeManagers( req, **params):
    return conferenceModif.RHConfRemoveManagers( req ).process( params )

def selectRegistrars( req, **params ):
    return conferenceModif.RHConfSelectRegistrars( req ).process( params )

def addRegistrars( req, **params ):
    return conferenceModif.RHConfAddRegistrars( req ).process( params )

def removeRegistrars( req, **params):
    return conferenceModif.RHConfRemoveRegistrars( req ).process( params )

def modifySessionCoordRights( req, **params ):
    return conferenceModif.RHModifSessionCoordRights( req ).process( params )

def grantSubmissionToAllSpeakers( req, **params ):
    return conferenceModif.RHConfGrantSubmissionToAllSpeakers( req ).process( params )

def grantModificationToAllConveners( req, **params ):
    return conferenceModif.RHConfGrantModificationToAllConveners( req ).process( params )

def removeAllSubmissionRights( req, **params ):
    return conferenceModif.RHConfRemoveAllSubmissionRights( req ).process( params )
