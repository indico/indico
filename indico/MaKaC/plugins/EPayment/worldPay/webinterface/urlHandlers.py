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

from MaKaC.webinterface.urlHandlers import URLHandler as MainURLHandler
from MaKaC.plugins.EPayment import worldPay

class EPURLHandler(MainURLHandler):
    
    _requestTag = ""
    
    def getURL( cls, target=None ):
        """Gives the full URL for the corresponding request handler. In case
            the target parameter is specified it will append to the URL the 
            the necessary parameters to make the target be specified in the url.
            
            Parameters:
                target - (Locable) Target object which must be uniquely 
                    specified in the URL so the destination request handler
                    is able to retrieve it. 
        """
        #url = MainURLHandler.getURL(target)
        url = cls._getURL()
        if target is not None:
            url.setParams( target.getLocator() )
        url.addParam( "EPaymentName", worldPay.pluginName )
        url.addParam( "requestTag", cls._requestTag )
        return url
    getURL = classmethod( getURL )



# URL for WorldPay configuration
class UHConfModifEPayment(EPURLHandler):
    _relativeURL = "confModifEpayment.py/modifModule"
    

class UHConfModifEPaymentWorldPay( UHConfModifEPayment ):
    _requestTag = "modifWorldPay"

class UHConfModifEPaymentWorldPayDataModif( UHConfModifEPayment ):
    _requestTag = "modifWorldPayData"
    
class UHConfModifEPaymentWorldPayPerformDataModif( UHConfModifEPayment ):
    _requestTag = "modifWorldPayPerformDataModif"




# URL for WorldPay callback
class UHPay(MainURLHandler):
    _relativeURL = "payment.py"

class UHPayConfirmWorldPay( UHPay ):
    _requestTag = "confirm"

class UHPayCancelWorldPay( UHPay ):
    _requestTag = "cancel"
