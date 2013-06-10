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

import MaKaC.webinterface.rh.ePaymentModif as ePaymentModif


def index(req, **params):
    return ePaymentModif.RHEPaymentModif( req ).process( params )

def changeStatus(req, **params):
    return ePaymentModif.RHEPaymentModifChangeStatus( req ).process( params )

def dataModif(req, **params):
    return ePaymentModif.RHEPaymentModifDataModification( req ).process( params )
    
def performDataModif(req, **params):
    return ePaymentModif.RHEPaymentModifPerformDataModification( req ).process( params )

def enableSection(req, **params):
    return ePaymentModif.RHEPaymentModifEnableSection( req ).process( params )

def modifModule(req, **params):
    return ePaymentModif.RHModifModule(req).process(params)
