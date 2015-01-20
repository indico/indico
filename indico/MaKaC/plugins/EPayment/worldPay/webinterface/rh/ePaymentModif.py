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


from MaKaC.plugins.EPayment.worldPay.webinterface.pages import ePayments
from MaKaC.plugins.EPayment.worldPay.webinterface import urlHandlers as localUrlHandlers
from MaKaC.plugins.EPayment.worldPay import MODULE_ID, epayment as ePayment


### classes for WorldPay integration

# world pay information page
class RHEPaymentmodifWorldPay( RHEPaymentModifBase ):
    _requestTag = "modifWorldPay"

    def _process( self ):
        p = ePayments.WPConfModifEPaymentWorldPay( self, self._conf)
        return p.display()


# world pay modification page
class RHEPaymentmodifWorldPayDataModif( RHEPaymentModifBase ):
    _requestTag = "modifWorldPayData"

    def _process( self ):
        p = ePayments.WPConfModifEPaymentWorldPayDataModif( self, self._conf)
        return p.display()


# submission page for configuration modifications
class RHEPaymentmodifWorldPayPerformDataModif( RHEPaymentModifBase ):
    _requestTag = "modifWorldPayPerformDataModif"

    def _checkParams( self, params ):
        RHEPaymentModifBase._checkParams( self, params)
        self._params = params
        self._cancel = params.has_key("cancel")

    def _process( self ):
        if not self._cancel:
            ses = self._conf.getModPay().getPayModByTag(MODULE_ID)
            ses.setValues(self._params)
        self._redirect(localUrlHandlers.UHConfModifEPaymentWorldPay.getURL(self._conf))


# two classes to take the callback from worldpay
class RHEPaymentConfirmWorldPay( RHConferenceBaseDisplay ):
    _requestTag = "confirm"

    def _checkProtection(self):
        # Just bypass everything else, as we want the payment service
        # to acknowledge the payment
        pass

    def _checkParams( self, params ):
        if not "confId" in params.keys():
            params["confId"] = params.get("M_confId","")
        if not "registrantId" in params.keys():
            params["registrantId"] = params.get("M_registrantId","")
        RHConferenceBaseDisplay._checkParams(self, params)
        self._regForm = self._conf.getRegistrationForm()
        self._params = params
        self._registrant = None
        regId = params.get("registrantId", "")
        if regId is not None:
            self._registrant = self._conf.getRegistrantById(regId)

    def _process( self ):
        regForm = self._conf.getRegistrationForm()
        if not regForm.isActivated() or not self._conf.hasEnabledSection("regForm"):
            p = registrationForm.WPRegFormInactive( self, self._conf )
            return p.display()
        else:
            if self._registrant is not None:

                if self._params.get('transStatus',"").lower() == 'y':
                    self._registrant.setPayed(True)
                    d={}
                    d["postcode"]=self._params.get('postcode',"")
                    d["email"]=self._params.get('email',"")
                    d["transId"]=self._params.get('transId',"")
                    d["compName"]=self._params.get('compName',"")
                    d["transStatus"]=self._params.get('transStatus',"")
                    d["countryMatch"]=self._params.get('countryMatch',"")
                    d["authMode"]=self._params.get('authMode',"")
                    d["amount"]=self._params.get('amount',"")
                    d["AVS"]=self._params.get('AVS',"")
                    d["authCost"]=self._params.get('authCost',"")
                    d["country"]=self._params.get('country',"")
                    d["lang"]=self._params.get('lang',"")
                    d["cartId"]=self._params.get('cartId',"")
                    d["name"]=self._params.get('name',"")
                    d["transTime"]=self._params.get('transTime',"")
                    d["desc"]=self._params.get('desc',"")
                    d["authAmount"]=self._params.get('authAmount',"")
                    d["rawAuthCode"]=self._params.get('rawAuthCode',"")
                    d["authAmountString"]=self._params.get('authAmountString',"")
                    d["address"]=self._params.get('address',"")
                    d["amountString"]=self._params.get('amountString',"")
                    d["cardType"]=self._params.get('cardType',"")
                    d["currency"]=self._params.get('currency',"")
                    d["cost"]=self._params.get('cost',"")
                    d["rawAuthMessage"]=self._params.get('rawAuthMessage',"")
                    d["countryString"]=self._params.get('countryString',"")
                    d["authCurrency"]=self._params.get('authCurrency',"")
                    d["payment_date"]= datetime.utcfromtimestamp(int(long(d["transTime"])/1000))
                    tr=ePayment.TransactionWorldPay(d)
                    self._registrant.setTransactionInfo(tr)
                    self._regForm.getNotification().sendEmailNewRegistrantConfirmPay(self._regForm,self._registrant)

                    p = ePayments.WPEPaymentWorldPayAccepted(self, self._conf, self._registrant )
                    d["registrantTitle"] = self._registrant.getTitle()
                    d["registrantFirstName"] = self._registrant.getFirstName()
                    d["registrantSurName"] = self._registrant.getSurName()
                    #d["registrant"] = self._registrant.getPosition()
                    d["registrantInstitution"] = self._registrant.getInstitution()
                    d["registrantAddress"] = self._registrant.getAddress()
                    d["registrantCity"] = self._registrant.getCity()
                    d["registrantCountry"] = self._registrant.getCountry()
                    d["registrantPhone"] = self._registrant.getPhone()
                    d["registrantFax"] = self._registrant.getFax()
                    d["registrantEmail"] = self._registrant.getEmail()
                    d["registrantPersonalHomepage"] = self._registrant.getPersonalHomepage()
                    return p.display(d)
                else:
                    d={}
                    d["postcode"]=self._params.get('postcode',"")
                    d["email"]=self._params.get('email',"")
                    d["transId"]=self._params.get('transId',"")
                    d["compName"]=self._params.get('compName',"")
                    d["transStatus"]=self._params.get('transStatus',"")
                    d["countryMatch"]=self._params.get('countryMatch',"")
                    d["authMode"]=self._params.get('authMode',"")
                    d["amount"]=self._params.get('amount',"")
                    d["AVS"]=self._params.get('AVS',"")
                    d["authCost"]=self._params.get('authCost',"")
                    d["country"]=self._params.get('country',"")
                    d["lang"]=self._params.get('lang',"")
                    d["cartId"]=self._params.get('cartId',"")
                    d["name"]=self._params.get('name',"")
                    d["transTime"]=self._params.get('transTime',"")
                    d["desc"]=self._params.get('desc',"")
                    d["authAmount"]=self._params.get('authAmount',"")
                    d["rawAuthCode"]=self._params.get('rawAuthCode',"")
                    d["authAmountString"]=self._params.get('authAmountString',"")
                    d["address"]=self._params.get('address',"")
                    d["amountString"]=self._params.get('amountString',"")
                    d["cardType"]=self._params.get('cardType',"")
                    d["currency"]=self._params.get('currency',"")
                    d["cost"]=self._params.get('cost',"")
                    d["rawAuthMessage"]=self._params.get('rawAuthMessage',"")
                    d["countryString"]=self._params.get('countryString',"")
                    d["authCurrency"]=self._params.get('authCurrency',"")
                    d["payment_date"]= datetime.utcfromtimestamp(int(long(d["transTime"])/1000))

                    p = ePayments.WPEPaymentWorldPayCancelled(self, self._conf, self._registrant )
                    d["registrantTitle"] = self._registrant.getTitle()
                    d["registrantFirstName"] = self._registrant.getFirstName()
                    d["registrantSurName"] = self._registrant.getSurName()
                    #d["registrant"] = self._registrant.getPosition()
                    d["registrantInstitution"] = self._registrant.getInstitution()
                    d["registrantAddress"] = self._registrant.getAddress()
                    d["registrantCity"] = self._registrant.getCity()
                    d["registrantCountry"] = self._registrant.getCountry()
                    d["registrantPhone"] = self._registrant.getPhone()
                    d["registrantFax"] = self._registrant.getFax()
                    d["registrantEmail"] = self._registrant.getEmail()
                    d["registrantPersonalHomepage"] = self._registrant.getPersonalHomepage()
                    return p.display(d)


class RHEPaymentCancelWorldPay( RHRegistrationFormDisplayBase ):
    _requestTag = "cancel"

    def _checkParams( self, params ):
        RHRegistrationFormDisplayBase._checkParams( self, params )
        self._registrant=None
        regId=params.get("registrantId","")
        if regId is not None:
            self._registrant=self._conf.getRegistrantById(regId)

    def _processIfActive( self ):
        if self._registrant is not None:
            p = ePayments.WPCancelEPaymentWorldPay(self, self._conf ,self._registrant)
            return p.display()
