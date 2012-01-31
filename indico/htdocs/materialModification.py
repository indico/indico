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

