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

from MaKaC.webinterface.rh import materialModif

if DEVELOPMENT:
    materialModif = reload( materialModif )


def index(req, **params):
    return materialModif.RHMaterialModification( req ).process( params )

def modify(req, **params):
    return materialModif.RHMaterialModifyData( req ).process( params )

def performModify(req, **params):
    return materialModif.RHMaterialPerformModifyData( req ).process( params )

def addLink(req, **params):
    return materialModif.RHMaterialAddLink( req ).process( params )

def performAddLink(req, **params):
    return materialModif.RHMaterialPerformAddLink( req ).process( params )

def addFile(req, **params):
    return materialModif.RHMaterialAddFile( req ).process( params )

def performAddFile(req, **params):
    return materialModif.RHMaterialPerformAddFile( req ).process( params )

def removeResources( req, **params ):
    return materialModif.RHMaterialRemoveResources( req ).process( params )

def selectMainResource( req, **params ):
    return materialModif.RHMaterialMainResourceSelect(req).process( params )

def performSelectMainResource( req, **params ):
    return materialModif.RHMaterialMainResourcePerformSelect(req).process( params )

