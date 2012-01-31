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

def index( req, **params ):
    return conferenceModif.RHConfModifPendingQueues( req ).process( params )

def actionSubmitters( req, **params ):
    return conferenceModif.RHConfModifPendingQueuesActionSubm( req ).process( params )

def actionManagers( req, **params ):
    return conferenceModif.RHConfModifPendingQueuesActionMgr( req ).process( params )

def actionCoordinators( req, **params ):
    return conferenceModif.RHConfModifPendingQueuesActionCoord( req ).process( params )

