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
  
##def modifYellowpay(req, **params):
##    return ePaymentModif.RHEPaymentmodifYellowPay( req ).process( params )
##   
##def modifYellowPayData(req, **params):
##    return ePaymentModif.RHEPaymentmodifYellowPayDataModif( req ).process( params )    
##
##def modifYellowPayPerformDataModif(req, **params):
##    return ePaymentModif.RHEPaymentmodifYellowPayPerformDataModif( req ).process( params )
##
##def modifPayPal(req, **params):
##    return ePaymentModif.RHEPaymentmodifPayPal( req ).process( params )
##   
##def modifPayPalData(req, **params):
##    return ePaymentModif.RHEPaymentmodifPayPalDataModif( req ).process( params )    
##
##def modifPayPalPerformDataModif(req, **params):
##    return ePaymentModif.RHEPaymentmodifPayPalPerformDataModif( req ).process( params )
##
##def modifWorldPay(req, **params):
##    return ePaymentModif.RHEPaymentmodifWorldPay( req ).process( params )
##
##def modifWorldPayData(req, **params):
##    return ePaymentModif.RHEPaymentmodifWorldPayDataModif( req ).process( params )
##
##def modifWorldPayPerformDataModif(req, **params):
##    return ePaymentModif.RHEPaymentmodifWorldPayPerformDataModif( req ).process( params )

def modifModule(req, **params):
    return ePaymentModif.RHModifModule(req).process(params)