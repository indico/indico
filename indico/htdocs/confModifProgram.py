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

from MaKaC.webinterface.rh import conferenceModif


def index( req, **params ):
    return conferenceModif.RHConfModifProgram( req ).process( params )


def addTrack( req, **params ):
    return conferenceModif.RHConfAddTrack( req ).process( params )


def performAddTrack( req, **params ):
    return conferenceModif.RHConfPerformAddTrack( req ).process( params )


def deleteTracks( req, **params ):
    return conferenceModif.RHConfDelTracks( req ).process( params )


def moveTrackUp(req,**params):
    return conferenceModif.RHProgramTrackUp( req ).process( params )


def moveTrackDown(req,**params):
    return conferenceModif.RHProgramTrackDown( req ).process( params )

def modifyDescription(req,**params):
    return conferenceModif.RHProgramDescription( req ).process( params )


#def addContribution( req, **params ):
#    return conferenceModif.RHConfAddContribution( req ).process( params )
#
#def performAddContribution( req, **params ):
#    return conferenceModif.RHConfPerformAddContribution( req ).process( params )
#
#def addBreak( req, **params ):
#    return conferenceModif.RHConfAddBreak( req ).process( params )
#
#def performAddBreak( req, **params ):
#    return conferenceModif.RHConfPerformAddBreak( req ).process( params )
#
#def modifyBreak( req, **params ):
#    return conferenceModif.RHConfModifyBreak( req ).process( params )
#
#def performModifyBreak( req, **params ):
#    return conferenceModif.RHConfPerformModifyBreak( req ).process( params )
