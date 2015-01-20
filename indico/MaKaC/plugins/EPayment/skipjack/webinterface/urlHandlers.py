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
from MaKaC.plugins.EPayment import skipjack


class EPURLHandler(MainURLHandler):
    _requestTag = ''

    @classmethod
    def getURL(cls, target=None):
        return super(EPURLHandler, cls).getURL(target, EPaymentName=skipjack.MODULE_ID, requestTag=cls._requestTag)


# URL for Skipjack configuration
class UHConfModifEPayment(EPURLHandler):
    _endpoint = 'event_mgmt.confModifEpayment-modifModule'


class UHConfModifEPaymentSkipjack( UHConfModifEPayment ):
    _requestTag = "modifSkipjack"

class UHConfModifEPaymentSkipjackDataModif( UHConfModifEPayment ):
    _requestTag = "modifSkipjackData"

class UHConfModifEPaymentSkipjackPerformDataModif( UHConfModifEPayment ):
    _requestTag = "modifSkipjackPerformDataModif"


# URL for Skipjack callback
class UHPay(EPURLHandler):
    _endpoint = 'misc.payment'


class UHPayConfirmSkipjack( UHPay ):
    _requestTag = "confirm"

class UHPayCancelSkipjack( UHPay ):
    _requestTag = "cancel"

class UHPayDisplayInfoSkipjack( UHPay ):
    _requestTag = "displayInfo"
