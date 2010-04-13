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

from MaKaC.webinterface.rh import materialDisplay

if DEVELOPMENT:
    materialDisplay = reload( materialDisplay )


def index(req, **params):
    return materialDisplay.RHMaterialDisplay( req ).process( params )

def removeResource(req, **params):
    return materialDisplay.RHMaterialDisplayRemoveResource( req ).process( params )

def submitResource(req, **params):
    return materialDisplay.RHMaterialDisplaySubmitResource( req ).process( params )

def accessKey(req, **params):
    return materialDisplay.RHMaterialDisplayStoreAccessKey( req ).process( params )

#def materialModification(req, **params):
#   return materialDisplay.RHMaterialDisplayModification( req ).process( params )

#def dataModification(req, **params):
#    return materialDisplay.RHMaterialDisplayDataModification( req ).process( params )

#def performDataModification(req, **params):
#    return materialDisplay.RHMaterialDisplayPerformDataModification( req ).process( params )

#def linkCreation(req, **params):
#    return materialDisplay.RHMaterialDisplayLinkCreation( req ).process( params )

#def performLinkCreation(req, **params):
#    return materialDisplay.RHMaterialDisplayPerformLinkCreation( req ).process( params )

#def fileCreation(req, **params):
#    return materialDisplay.RHMaterialDisplayFileCreation( req ).process( params )

#def performFileCreation(req, **params):
#    return materialDisplay.RHMaterialDisplayPerformFileCreation( req ).process( params )

#def removeResources(req, **params):
#    return materialDisplay.RHMaterialDisplayRemoveResources( req ).process( params )

