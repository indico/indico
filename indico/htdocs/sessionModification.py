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

from MaKaC.webinterface.rh import sessionModif


def index(req, **params):
    return sessionModif.RHSessionModification( req ).process( params )

def modify( req, **params ):
    return sessionModif.RHSessionDataModification( req ).process( params )

def modifyDates( req, **params ):
    return sessionModif.RHSessionDatesModification( req ).process( params )

def convenerSearch( req, **params ):
    return sessionModif.RHSessionDataModificationConvenerSearch( req ).process( params )
    
def convenerNew( req, **params ):
    return sessionModif.RHSessionDataModificationConvenerNew( req ).process( params )
    
def personAdd( req, **params ):
    return sessionModif.RHSessionDataModificationPersonAdd( req ).process( params )

def newConvenerSearch( req, **params ):
    return sessionModif.RHSessionDataModificationNewConvenerSearch( req ).process( params )    

def newConvenerCreate( req, **params ):    
    return sessionModif.RHSessionDataModificationNewConvenerCreate( req ).process( params )    

def convenerAdd( req, **params ):
    return sessionModif.RHSessionDataModificationConvenerAdd( req ).process( params )

def close( req, **params ):
    return sessionModif.RHSessionClose( req ).process( params )

def open( req, **params ):
    return sessionModif.RHSessionOpen( req ).process( params )

def newConvener(req,**params):
    return sessionModif.RHConvenerNew( req ).process( params)

def remConveners(req, **args):
    return sessionModif.RHConvenersRem( req ).process( args )

def editConvener(req,**params):
    return sessionModif.RHConvenerEdit( req ).process( params)

def addMaterial( req, **params ):
    return sessionModif.RHSessionAddMaterial( req ).process( params )
    
def performAddMaterial( req, **params ):
    return sessionModif.RHSessionPerformAddMaterial( req ).process( params )
    
def removeMaterials( req, **params ):
    return sessionModif.RHSessionRemoveMaterials( req ).process( params )

def materialsAdd(req, **params):
    return sessionModif.RHMaterialsAdd(req).process(params)

def importContrib( req, **params ):
    return sessionModif.RHSessionImportContrib( req ).process( params )

def addContribs( req, **params ):
    return sessionModif.RHAddContribs( req ).process( params )

def addContribs( req, **params ):
    return sessionModif.RHAddContribs( req ).process( params )

def contribList( req, **params ):
    return sessionModif.RHContribList( req ).process( params )

def editContrib( req, **params ):
    return sessionModif.RHContribListEditContrib( req ).process( params )

def contribAction( req, **params ):
    return sessionModif.RHContribsActions( req ).process( params )

def contribQuickAccess( req, **params ):
    return sessionModif.RHContribQuickAccess(req).process(params)

def participantList( req, **params ):
    return sessionModif.RHContribsParticipantList(req).process(params)

def contribsToPDF( req, **params ):
    return sessionModif.RHContribsToPDF(req).process(params)

def materials(req, **params):
    return sessionModif.RHMaterials( req ).process( params )
