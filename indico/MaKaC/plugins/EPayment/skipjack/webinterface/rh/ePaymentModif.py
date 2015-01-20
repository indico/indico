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


from MaKaC.plugins.EPayment.skipjack.webinterface.pages import ePayments
from MaKaC.plugins.EPayment.skipjack.webinterface import urlHandlers as localUrlHandlers
from MaKaC.plugins.EPayment.skipjack import MODULE_ID, epayment as ePayment

from MaKaC.errors import AccessError
from MaKaC.webinterface.pages import registrationForm


### classes for Skipjack integration

# Skipjack information page
class RHEPaymentmodifSkipjack( RHEPaymentModifBase ):
    _requestTag = "modifSkipjack"

    def _process( self ):
        p = ePayments.WPConfModifEPaymentSkipjack( self, self._conf)
        return p.display()


# skipjack modification page
class RHEPaymentmodifSkipjackDataModif( RHEPaymentModifBase ):
    _requestTag = "modifSkipjackData"

    def _process( self ):
        p = ePayments.WPConfModifEPaymentSkipjackDataModif( self, self._conf)
        return p.display()


# submission page for configuration modifications
class RHEPaymentmodifSkipjackPerformDataModif( RHEPaymentModifBase ):
    _requestTag = "modifSkipjackPerformDataModif"

    def _checkParams( self, params ):
        RHEPaymentModifBase._checkParams( self, params)
        self._params = params
        self._cancel = params.has_key("cancel")

    def _process( self ):
        if not self._cancel:
            ses = self._conf.getModPay().getPayModByTag(MODULE_ID)
            ses.setValues(self._params)
        self._redirect(localUrlHandlers.UHConfModifEPaymentSkipjack.getURL(self._conf))


# two classes to take the callback from skipjack
class RHEPaymentConfirmSkipjack( RHConferenceBaseDisplay ):
    _requestTag = "confirm"

    def _checkProtection(self):
        # Just bypass everything else, as we want the payment service
        # to acknowledge the payment
        pass

    def _checkParams( self, params ):
        #
        #skipjack does not allow for the sending of arbitrary variables.  We are
        #using the user defined fields to send the confid and the registrant id.
        #
        if not "confId" in params.keys():
            params["confId"] = params.get("UserDefined1","")
        if not "registrantId" in params.keys():
            params["registrantId"] = params.get("UserDefined2","")
        #_checkParams sets the conf field.
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
                if self._params.get('szIsApproved',"0") != '0':
                    self._registrant.setPayed(True)
                    d={}
                    d["shiptostate"]=self._params.get('shiptostate',"")
                    d["registrantId"]=self._params.get('registrantId',"")
                    d["shiptoname"]=self._params.get('shiptoname',"")
                    d["streetaddress"]=self._params.get('streetaddress',"")
                    d["szTransactionFileName"]=self._params.get('szTransactionFileName',"")
                    d["month"]=self._params.get('month',"")
                    d["year"]=self._params.get('year',"")
                    d["szAuthorizationResponseCode"]=self._params.get('szAuthorizationResponseCode',"")
                    d["streetaddress2"]=self._params.get('streetaddress2',"")
                    d["szOrderNumber"]=self._params.get('szOrderNumber',"")
                    d["accountnumber"]=self._params.get('accountnumber',"")
                    d["zipcode"]=self._params.get('zipcode',"")
                    d["szAVSResponseCode"]=self._params.get('szAVSResponseCode',"")
                    d["szCVV2ResponseCode"]=self._params.get('szCVV2ResponseCode',"")
                    d["Phone"]=self._params.get('Phone',"")
                    d["state"]=self._params.get('state',"")
                    d["shiptostreetaddress2"]=self._params.get('shiptostreetaddress2',"")
                    d["shiptozipcode"]=self._params.get('shiptozipcode',"")
                    d["transactionamount"]=self._params.get('transactionamount',"")
                    d["sjname"]=self._params.get('sjname',"")
                    d["szCVV2ResponseMessage"]=self._params.get('szCVV2ResponseMessage',"")
                    d["shiptocity"]=self._params.get('shiptocity',"")
                    d["orderstring"]=self._params.get('orderstring',"")
                    d["szAVSResponseMessage"]=self._params.get('szAVSResponseMessage',"")
                    d["szCAVVResponseCode"]=self._params.get('szCAVVResponseCode',"")
                    d["shiptophone"]=self._params.get('shiptophone',"")
                    d["country"]=self._params.get('country',"")
                    d["shiptostreetaddress"]=self._params.get('shiptostreetaddress',"")
                    d["szTransactionAmount"]=self._params.get('szTransactionAmount',"")
                    d["email"]=self._params.get('email',"")
                    d["city"]=self._params.get('city',"")
                    d["requestTag"]=self._params.get('requestTag',"")

                    tr=ePayment.TransactionSkipjack(d)

                    self._registrant.setTransactionInfo(tr)
                    self._regForm.getNotification().sendEmailNewRegistrantConfirmPay(self._regForm,self._registrant)

                    p = ePayments.WPEPaymentSkipjackAccepted(self, self._conf, self._registrant )
                    return p.display()
                else:
                    d={}
                    d["shiptostate"]=self._params.get('shiptostate',"")
                    d["registrantId"]=self._params.get('registrantId',"")
                    d["shiptoname"]=self._params.get('shiptoname',"")
                    d["szAuthorizationDeclinedMessage"]=self._params.get('szAuthorizationDeclinedMessage',"")
                    d["streetaddress"]=self._params.get('streetaddress',"")
                    d["szTransactionFileName"]=self._params.get('szTransactionFileName',"")
                    d["year"]=self._params.get('year',"")
                    d["szAuthorizationResponseCode"]=self._params.get('szAuthorizationResponseCode',"")
                    d["streetaddress2"]=self._params.get('streetaddress2',"")
                    d["szOrderNumber"]=self._params.get('szOrderNumber',"")
                    d["accountnumber"]=self._params.get('accountnumber',"")
                    d["zipcode"]=self._params.get('zipcode',"")
                    d["szAVSResponseCode"]=self._params.get('szAVSResponseCode',"")
                    d["szCVV2ResponseCode"]=self._params.get('szCVV2ResponseCode',"")
                    d["Phone"]=self._params.get('Phone',"")
                    d["state"]=self._params.get('state',"")
                    d["shiptostreetaddress2"]=self._params.get('shiptostreetaddress2',"")
                    d["shiptozipcode"]=self._params.get('shiptozipcode',"")
                    d["transactionamount"]=self._params.get('transactionamount',"")
                    d["sjname"]=self._params.get('sjname',"")
                    d["szCVV2ResponseMessage"]=self._params.get('szCVV2ResponseMessage',"")
                    d["shiptocity"]=self._params.get('shiptocity',"")
                    d["orderstring"]=self._params.get('orderstring',"")
                    d["szAVSResponseMessage"]=self._params.get('szAVSResponseMessage',"")
                    d["szCAVVResponseCode"]=self._params.get('szCAVVResponseCode',"")
                    d["shiptophone"]=self._params.get('shiptophone',"")
                    d["month"]=self._params.get('month',"")
                    d["country"]=self._params.get('country',"")
                    d["shiptostreetaddress"]=self._params.get('shiptostreetaddress',"")
                    d["szTransactionAmount"]=self._params.get('szTransactionAmount',"")
                    d["email"]=self._params.get('email',"")
                    d["city"]=self._params.get('city',"")
                    d["requestTag"]=self._params.get('requestTag',"")
                    p = ePayments.WPEPaymentSkipjackCancelled(self, self._conf, self._registrant, d["szAuthorizationDeclinedMessage"])
                    return p.display()


class RHEPaymentCancelSkipjack( RHRegistrationFormDisplayBase ):
    _requestTag = "cancel"

    def _checkParams( self, params ):
        RHRegistrationFormDisplayBase._checkParams( self, params )
        self._registrant=None
        regId=params.get("registrantId","")
        if regId is not None:
            self._registrant=self._conf.getRegistrantById(regId)

    def _processIfActive( self ):
        if self._registrant is not None:
            p = ePayments.WPCancelEPaymentSkipjack(self, self._conf ,self._registrant)
            return p.display()

class RHEPaymentDisplayInfoSkipjack( RHConferenceBaseDisplay ):
    _requestTag = "displayInfo"

    def _checkProtection( self ):
        if self._getUser() is None or self._registrant is None or (self._registrant.getAvatar().getId() != self._getUser().getId()):
            raise AccessError("Indico cannot display epayment information without being logged in")


    def _checkParams( self, params ):
        #
        #skipjack does not allow for the sending of arbitrary variables.  We are
        #using the user defined fields to send the confid and the registrant id.
        #
        if not "confId" in params.keys():
            params["confId"] = params.get("UserDefined1","")
        if not "registrantId" in params.keys():
            params["registrantId"] = params.get("UserDefined2","")
        #_checkParams sets the conf field.
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
            p = ePayments.WPEPaymentSkipjackDisplayInfo(self, self._conf, self._registrant )
            return p.display()
