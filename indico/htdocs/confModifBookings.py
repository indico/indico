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

from MaKaC.webinterface.rh import conferenceModif

def index(req, **params):
    return conferenceModif.RHConfModifBookings( req ).process( params )

def createBookingVRVS(req, **args ):
    return conferenceModif.RHBookingsVRVS( req ).process( args )

def performBookingVRVS(req, **args ):
    return conferenceModif.RHBookingsVRVSPerform( req ).process( args )

def performBookingAction(req, **args):
    return conferenceModif.RHBookingListModifAction(req).process (args)

def BookingDetail(req, **args):
    return conferenceModif.RHBookingDetail(req).process(args)

def performBookingDeletion(req, **args):
    return conferenceModif.RHBookingListDelete(req).process (args)

def performBookingModification(req, **args):
    return conferenceModif.RHBookingListModification(req).process (args)
