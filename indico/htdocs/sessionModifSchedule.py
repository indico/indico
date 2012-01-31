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

from MaKaC.webinterface.rh import sessionModif


def index( req, **params ):
    return sessionModif.RHSessionModifSchedule( req ).process( params )

def slotNew( req, **params ):
    return sessionModif.RHSlotNew(req).process(params)

def slotRem( req, **params ):
    return sessionModif.RHSlotRem(req).process(params)

def slotCalc( req, **params ):
    return sessionModif.RHSlotCalc(req).process(params)

def slotEdit( req, **params ):
    return sessionModif.RHSlotEdit(req).process(params)

def slotCompact( req, **params ):
    return sessionModif.RHSlotCompact(req).process(params)

def fitSlot( req, **params ):
    return sessionModif.RHFitSlot(req).process(params)

def fitSession( req, **params ):
    return sessionModif.RHFitSession(req).process(params)

def moveUpEntry(req,**params):
    return sessionModif.RHSlotMoveUpEntry(req).process(params)

def moveDownEntry(req,**params):
    return sessionModif.RHSlotMoveDownEntry(req).process(params)

def reducedScheduleAction( req, **params ):
    return sessionModif.RHReducedSessionScheduleAction( req ).process( params )

def addContrib( req, **params ):
    return sessionModif.RHScheduleAddContrib( req ).process( params )

def performNewContrib( req, **params ):
    return sessionModif.RHSchedulePerformNewContrib( req ).process( params )

def performAddContrib( req, **params ):
    return sessionModif.RHSessionPerformAddContribution( req ).process( params )

def addBreak( req, **params ):
    return sessionModif.RHSessionAddBreak( req ).process( params )

def performAddBreak( req, **params ):
    return sessionModif.RHSessionPerformAddBreak( req ).process( params )

def performModifyBreak( req, **params ):
    return sessionModif.RHSessionPerformModifyBreak( req ).process( params )

def delItems( req, **params ):
    return sessionModif.RHSessionDelSchItems( req ).process( params )

def editContrib( req, **params ):
    return sessionModif.RHSchEditContrib( req ).process( params )

#def editBreak( req, **params ):
#    return sessionModif.RHSchEditBreak( req ).process( params )

def modifyBreak( req, **params ):
    return sessionModif.RHSessionModifyBreak( req ).process( params )

def performModifyBreak( req, **params ):
    return sessionModif.RHSessionPerformModifyBreak( req ).process( params )

def relocate(req, **params):
    return sessionModif.RHRelocate( req ).process( params )
