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

import MaKaC.webinterface.rh.conferenceModif as conferenceModif


def index( req, **params ):
    return conferenceModif.RHAbstractList( req ).process( params )

def abstractsActions( req, **params ):
    return conferenceModif.RHAbstractsActions( req ).process( params )

def newAbstract( req, **params ):
    return conferenceModif.RHNewAbstract( req ).process( params )

def participantList( req, **params ):
    return conferenceModif.RHAbstractsParticipantList( req ).process( params )

def mergeAbstracts( req, **params ):
    return conferenceModif.RHAbstractsMerge( req ).process( params )