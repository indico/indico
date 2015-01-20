# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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

from MaKaC.webinterface.urlHandlers import URLHandler as MainURLHandler
from MaKaC.plugins.EPayment import worldPay


class EPURLHandler(MainURLHandler):
    _requestTag = ''

    @classmethod
    def getURL(cls, target=None):
        return super(EPURLHandler, cls).getURL(target, EPaymentName=worldPay.MODULE_ID, requestTag=cls._requestTag)


# URL for WorldPay configuration
class UHConfModifEPayment(EPURLHandler):
    _endpoint = 'event_mgmt.confModifEpayment-modifModule'


class UHConfModifEPaymentWorldPay( UHConfModifEPayment ):
    _requestTag = "modifWorldPay"

class UHConfModifEPaymentWorldPayDataModif( UHConfModifEPayment ):
    _requestTag = "modifWorldPayData"

class UHConfModifEPaymentWorldPayPerformDataModif( UHConfModifEPayment ):
    _requestTag = "modifWorldPayPerformDataModif"


# URL for WorldPay callback
class UHPay(MainURLHandler):
    _endpoint = 'misc.payment'

class UHPayConfirmWorldPay( UHPay ):
    _requestTag = "confirm"

class UHPayCancelWorldPay( UHPay ):
    _requestTag = "cancel"
