

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
from flask import request

import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.pages.epayments as ePayments
import MaKaC.epayment as ePayment
from datetime import datetime
import MaKaC.webinterface.rh.conferenceModif as conferenceModif
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay
from MaKaC.errors import FormValuesError, MaKaCError
from MaKaC.common import HelperMaKaCInfo
from MaKaC.i18n import _
from MaKaC.webinterface.pages import registrationForm
from MaKaC.plugins.base import pluginId

from MaKaC.plugins.EPayment.payPal import MODULE_ID



class RHEPaymentModifBase( conferenceModif.RHConferenceModifBase ):

    def _checkProtection( self ):
        conferenceModif.RHConferenceModifBase._checkProtection(self)

class RHEPaymentModif( RHEPaymentModifBase ):

    def _process( self ):
        p = ePayments.WPConfModifEPayment( self, self._conf )
        return p.display()

class RHEPaymentModifChangeStatus( RHEPaymentModifBase ):

    def _checkParams( self, params ):
        RHEPaymentModifBase._checkParams( self, params )
        self._newStatus = params["changeTo"]

    def _process( self ):
        epay = self._conf.getModPay()
        if self._newStatus == "True":
            epay.activate()
        else:
            epay.deactivate()
        self._redirect(urlHandlers.UHConfModifEPayment.getURL(self._conf))

class RHEPaymentModifDataModification( RHEPaymentModifBase ):

    def _process( self ):
        p = ePayments.WPConfModifEPaymentDataModification( self, self._conf )
        return p.display()

class RHEPaymentModifPerformDataModification( RHEPaymentModifBase ):

    def _checkParams( self, params ):
        RHEPaymentModifBase._checkParams( self, params )
        self._cancel = params.has_key("cancel")


    def _process( self ):
        if not self._cancel:
            modpay = self._conf.getModPay()
            params = self._getRequestParams()
            #modpay.getModPayLater().setValues(params)
            modpay.setPaymentDetails(params.get("detailPayment", ""))
            modpay.setPaymentSpecificConditions(params.get("specificConditionsPayment", ""))
            modpay.setPaymentSuccessMsg(params.get("successMsgPayment", ""))
            modpay.setPaymentReceiptMsg(params.get("receiptMsgPayment", ""))
            from MaKaC.common import HelperMaKaCInfo
            minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
            al = minfo.getAdminList()
            if al.isAdmin( self._getUser() ):
                modpay.setPaymentConditions(params.get("conditionsPayment", ""))
                modpay.setPaymentConditionsEnabled(params.has_key("conditionsEnabled"))
            self._conf.getRegistrationForm().setCurrency(params.get("Currency",""))
        self._redirect(urlHandlers.UHConfModifEPayment.getURL(self._conf))


class RHEPaymentModifEnableSection( RHEPaymentModifBase ):

    def _checkParams( self, params ):
        RHEPaymentModifBase._checkParams( self, params )
        self._epayment = params.get("epayment", "")

    def _process( self ):
        modPay = self._conf.getModPay().getModPayById(self._epayment)
        if modPay is not None:
            modPay.setEnabled(not modPay.isEnabled())
        self._redirect(urlHandlers.UHConfModifEPayment.getURL(self._conf))


class RHEPaymentmodifPayPalPerformDataModif( RHEPaymentModifBase ):

    def _checkParams( self, params ):
        RHEPaymentModifBase._checkParams( self, params )
        self._params=params
        self._cancel = params.has_key("cancel")

    def _process( self ):
        if not self._cancel:
            ses = self._conf.getModPay().getPayModByTag(MODULE_ID)
            ses.setValues(self._params)
        self._redirect(urlHandlers.UHConfModifEPaymentPayPal.getURL(self._conf))

####################################################################################
class RHRegistrationFormDisplayBase( RHConferenceBaseDisplay ):
    #_uh = urlHandlers.UHConfRegistrationFormDisplay

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams(self, params)
        self._regForm = self._conf.getRegistrationForm()

    def _getLoginURL( self ):
        urlLogin = str(urlHandlers.UHConfRegistrationFormSignIn.getURL(self._conf, request.url))
        from indico.core.config import Config
        if Config.getInstance().getLoginURL().startswith("https"):
            urlLogin = urlLogin.replace("http://", "https://")
        return urlLogin

    def _processIfActive( self ):
        """only override this method if the RegForm must be activated for
            carrying on the handler execution"""
        return "regForm"

    def _checkProtection( self ):
        RHConferenceBaseDisplay._checkProtection(self)
        if self._regForm.isMandatoryAccount() and self._getUser() == None:
            self._redirect( self._getLoginURL() )
            self._doProcess = False

    def _process( self ):
        #if the RegForm is not activated we show up a form informing about that.
        #   This must be done at RH level because there can be some RH not
        #   displaying pages.
        regForm = self._conf.getRegistrationForm()
        if not regForm.isActivated() or not self._conf.hasEnabledSection("regForm"):
            p = registrationForm.WPRegFormInactive( self, self._conf )
            return p.display()
        else:
            return self._processIfActive()


class RHModifModule:
    def __init__(self, req):
        self._req = req

    def process(self, params):
        from MaKaC.plugins import PluginLoader
        epaymentModules = PluginLoader.getPluginsByType("EPayment")
        module = None
        for mod in epaymentModules:
            if mod.MODULE_ID == params.get("EPaymentName","No module name"):
                module = mod
                break

        if module:
            try:
                rhmod = module.webinterface.rh
            except:
                raise MaKaCError("%s"%module)
            requestTag = params.get("requestTag", "No requestTag")
            rh = rhmod.getRHByTag(rhmod, requestTag)
            if rh:
                return rh(self._req).process(params)
            return "Request handler not found"
        return "Module not found"
