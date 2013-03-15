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
def effectuer(req, **params):
    return ePaymentModif.RHEPaymentconfirmYellowPay( req ).process( params )

def noneffectuer(req, **params):
    return ePaymentModif.RHEPaymentNotconfirmYellowPay( req ).process( params )

def annuler(req, **params):
    return ePaymentModif.RHEPaymentCancelYellowPay( req ).process( params )
    
def params(req, **params):    
    return ePaymentModif.RHEPaymentValideParamYellowPay( req ).process( params )
