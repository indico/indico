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

import MaKaC.webinterface.rh.conferenceDisplay as conferenceDisplay


def index(req, **params):
    return conferenceDisplay.RHConferenceDisplay( req ).process( params )

def getLogo(req, **params):
    return conferenceDisplay.RHConferenceGetLogo( req ).process( params )

def getCSS(req, **params):
    return conferenceDisplay.RHConferenceGetCSS( req ).process( params )

def getPic(req, **params):
    return conferenceDisplay.RHConferenceGetPic( req ).process( params )

def abstractBook(req, **params):
    return conferenceDisplay.RHAbstractBook(req).process(params)

def abstractBookLatex(req, **params):
    return conferenceDisplay.RHConferenceLatexPackage(req).process(params)

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

def matPkg( req, **params ):
    return conferenceDisplay.RHFullMaterialPackage( req ).process( params )

def performMatPkg( req, **params ):
    return conferenceDisplay.RHFullMaterialPackagePerform( req ).process( params )

def next(req, **params):
    return conferenceDisplay.RHRelativeEvent(req, 'next').process(params)

def prev(req, **params):
    return conferenceDisplay.RHRelativeEvent(req, 'prev').process(params)
