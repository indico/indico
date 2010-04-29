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

import MaKaC.webinterface.rh.conferenceDisplay as conferenceDisplay


def index(req, **params):
    return conferenceDisplay.RHConferenceDisplay( req ).process( params )

def getLogo(req, **params):
    return conferenceDisplay.RHConferenceGetLogo( req ).process( params )

def getCSS(req, **params):
    return conferenceDisplay.RHConferenceGetCSS( req ).process( params )

def getPic(req, **params):
    return conferenceDisplay.RHConferenceGetPic( req ).process( params )

def closeMenu(req, **params):
    return conferenceDisplay.RHConferenceMenuClose( req ).process( params )

def openMenu(req, **params):
    return conferenceDisplay.RHConferenceMenuOpen( req ).process( params )

def abstractBook(req, **params):
    return conferenceDisplay.RHAbstractBook(req).process(params)

def abstractBookLatex(req, **params):
    return conferenceDisplay.RHConferenceLatexPackage(req).process(params)

def abstractBookPerform(req,**params):
    return conferenceDisplay.RHAbstractBookPerform(req).process(params)

def accessKey(req, **params):
    return conferenceDisplay.RHConferenceAccessKey(req).process(params)

def forceAccessKey(req, **params):
    return conferenceDisplay.RHConferenceForceAccessKey(req).process(params)

def ical(req, **params):
    return conferenceDisplay.RHConferenceToiCal( req ).process( params )

def xml(req, **params):
    return conferenceDisplay.RHConferenceToXML( req ).process( params )

def marcxml(req, **params):
    return conferenceDisplay.RHConferenceToMarcXML( req ).process( params )

def writeMinutes(req, **params):
    return conferenceDisplay.RHWriteMinutes( req ).process( params )

def submit(req, **params):
    return conferenceDisplay.RHSubmitMaterial(req).process(params)

def matPkg( req, **params ):
    return conferenceDisplay.RHFullMaterialPackage( req ).process( params )

def performMatPkg( req, **params ):
    return conferenceDisplay.RHFullMaterialPackagePerform( req ).process( params )
