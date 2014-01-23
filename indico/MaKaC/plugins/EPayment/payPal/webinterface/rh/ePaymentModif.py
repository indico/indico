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

from MaKaC.webinterface.rh.ePaymentModif import RHEPaymentModifBase, RHConferenceBaseDisplay, RHRegistrationFormDisplayBase
import MaKaC.webinterface.urlHandlers as urlHandlers
from datetime import datetime
from MaKaC.common.timezoneUtils import nowutc


from MaKaC.plugins.EPayment.payPal.webinterface.pages import ePayments
from MaKaC.plugins.EPayment.payPal.webinterface import urlHandlers as localUrlHandlers
from MaKaC.plugins.EPayment.payPal import epayment as ePayment
from MaKaC.plugins.EPayment.payPal import MODULE_ID


class RHEPaymentmodifPayPal( RHEPaymentModifBase ):
    _requestTag = "modifPayPal"

    def _process( self ):
        p = ePayments.WPConfModifEPaymentPayPal( self, self._conf )
        return p.display()

class RHEPaymentmodifPayPalDataModif( RHEPaymentModifBase ):
    _requestTag = "modifPayPalData"

    def _process( self ):
        p = ePayments.WPConfModifEPaymentPayPalDataModif( self, self._conf )
        return p.display()

class RHEPaymentmodifPayPalPerformDataModif( RHEPaymentModifBase ):
    _requestTag = "modifPayPalPerformDataModif"

    def _checkParams( self, params ):
        RHEPaymentModifBase._checkParams( self, params )
        self._params=params
        self._cancel = params.has_key("cancel")

    def _process( self ):
        if not self._cancel:
            ses = self._conf.getModPay().getPayModByTag(MODULE_ID)
            ses.setValues(self._params)
        self._redirect(localUrlHandlers.UHConfModifEPaymentPayPal.getURL(self._conf))




class RHEPaymentconfirmPayPal( RHRegistrationFormDisplayBase ):
    _requestTag = "confirm"

    def _checkParams( self, params ):
        RHRegistrationFormDisplayBase._checkParams( self, params )
        self._registrant=None
        regId= params.get("registrantId","")
        if regId is not None:
            self._registrant=self._conf.getRegistrantById(regId)

    def _processIfActive( self ):
        if self._registrant is not None:
            p = ePayments.WPconfirmEPaymentPayPal( self,self._conf,self._registrant)
            return p.display()

class RHEPaymentCancelPayPal( RHRegistrationFormDisplayBase ):
    _requestTag = "cancel"

    def _checkParams( self, params ):
        RHRegistrationFormDisplayBase._checkParams( self, params )
        self._registrant=None
        regId=params.get("registrantId","")
        if regId is not None:
            self._registrant=self._conf.getRegistrantById(regId)

    def _processIfActive( self ):
        if self._registrant is not None:
            p = ePayments.WPCancelEPaymentPayPal( self,self._conf ,self._registrant)
            return p.display()


class RHEPaymentValideParamPayPal( RHConferenceBaseDisplay ):
    _requestTag = "params"

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams(self, params)
        self._regForm = self._conf.getRegistrationForm()
        self._params=params
        self._registrant=None
        regId=params.get("registrantId","")
        if regId is not None:
            self._registrant=self._conf.getRegistrantById(regId)

    def _checkProtection(self):
        # Just bypass everything else, as we want the payment service
        # to acknowledge the payment
        pass

    def _process( self ):
        regForm = self._conf.getRegistrationForm()
        if not regForm.isActivated() or not self._conf.hasEnabledSection("regForm"):
            p = registrationForm.WPRegFormInactive( self, self._conf )
            return p.display()
        else:
            if self._registrant is not None:
                self._registrant.setPayed(True)
                d={}
                d["payment_date"]=nowutc()
                d["payer_id"]=self._params.get("payer_id")
                d["mc_currency"]=self._params.get("mc_currency")
                d["mc_gross"]=self._params.get("mc_gross")
                d["verify_sign"]=self._params.get("verify_sign")
                tr=ePayment.TransactionPayPal(d)
                self._registrant.setTransactionInfo(tr)
                self._regForm.getNotification().sendEmailNewRegistrantConfirmPay(self._regForm,self._registrant )



