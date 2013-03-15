# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

from MaKaC.webinterface.rh import contribDisplay


def index(req, **params):
    return contribDisplay.RHContributionDisplay( req ).process( params )


def xml( req, **params ):
    return contribDisplay.RHContributionToXML( req ).process( params )


def pdf( req, **params ):
    return contribDisplay.RHContributionToPDF( req ).process( params )


def ical( req, **params ):
    return contribDisplay.RHContributionToiCal( req ).process( params )

def marcxml( req, **params ):
    return contribDisplay.RHContributionToMarcXML( req ).process( params )

def removeMaterial(req, **params):
    return contribDisplay.RHContributionDisplayRemoveMaterial(req).process(params)
