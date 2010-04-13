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
    return materialModif.RHMaterialModifAC( req ).process( params )

def setPrivacy(req, **params):
    return materialModif.RHMaterialSetPrivacy( req ).process( params )

def setVisibility(req, **params):
    return materialModif.RHMaterialSetVisibility( req ).process( params )

def setAccessKey(req, **params):
    return materialModif.RHMaterialSetAccessKey( req ).process( params )

def selectAllowed(req, **params):
    return materialModif.RHMaterialSelectAllowed( req ).process( params )

def addAllowed(req, **params):
    return materialModif.RHMaterialAddAllowed( req ).process( params )

def removeAllowed(req, **params):
    return materialModif.RHMaterialRemoveAllowed( req ).process( params )

def addDomains(req, **params):
    return materialModif.RHMaterialAddDomains( req ).process( params )

def removeDomains(req, **params):
    return materialModif.RHMaterialRemoveDomains( req ).process( params )
