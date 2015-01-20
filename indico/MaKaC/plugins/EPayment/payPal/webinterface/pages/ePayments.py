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

import MaKaC.webinterface.pages.conferences as conferences
import MaKaC.webinterface.pages.registrationForm as registrationForm
from MaKaC.webinterface import wcomponents
from xml.sax.saxutils import quoteattr
from indico.core import config as Configuration
from MaKaC.webinterface import urlHandlers
import MaKaC
from MaKaC.i18n import _


from MaKaC.plugins.EPayment.payPal import MODULE_ID
from MaKaC.plugins.EPayment.payPal.webinterface.wcomponents import WTemplated
from MaKaC.plugins.EPayment.payPal.webinterface import urlHandlers as localUrlHandlers



class WPConfModifEPaymentPayPalBase(registrationForm.WPConfModifRegFormBase):

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main", _("Main"), \
                localUrlHandlers.UHConfModifEPaymentPayPal.getURL( self._conf ) )
        wf = self._rh.getWebFactory()
        if wf:
            wf.customiseTabCtrl( self._tabCtrl )
        self._setActiveTab()

    def _setActiveTab( self ):
        pass

    def _setActiveSideMenuItem(self):
        self._regFormMenuItem.setActive(True)

    def _getPageContent( self, params ):
        self._createTabCtrl()
        banner = wcomponents.WEpaymentBannerModif(self._conf.getModPay().getPayModByTag(MODULE_ID), self._conf).getHTML()
        html = wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )
        return banner+html

    def _getTabContent( self, params ):
        return "nothing"

class WPConfModifEPaymentPayPal( WPConfModifEPaymentPayPalBase ):

    def _getTabContent( self, params ):
        wc = WConfModifEPaymentPayPal(self._conf)
        p = {
             'dataModificationURL': quoteattr(str(localUrlHandlers.UHConfModifEPaymentPayPalDataModif.getURL( self._conf )))
            }
        return wc.getHTML(p)

class WConfModifEPaymentPayPal( WTemplated ):

    def __init__( self, conference ):
        self._conf = conference

    def getVars( self ):
        vars = WTemplated.getVars(self)
        modPayPal = self._conf.getModPay().getPayModByTag(MODULE_ID)
        vars["title"] = modPayPal.getTitle()
        vars["url"] = modPayPal.getUrl()
        vars["business"] =  modPayPal.getBusiness()
        return vars

class WPConfModifEPaymentPayPalDataModif( WPConfModifEPaymentPayPalBase ):

    def _getTabContent( self, params ):
        wc = WConfModifEPaymentPayPalDataModif(self._conf)
        p = {'postURL': quoteattr(str(localUrlHandlers.UHConfModifEPaymentPayPalPerformDataModif.getURL( self._conf )))
            }
        return wc.getHTML(p)

class WConfModifEPaymentPayPalDataModif( WTemplated ):

    def __init__( self, conference ):
        self._conf = conference

    def getVars( self ):
        vars = WTemplated.getVars(self)
        modPayPal = self._conf.getModPay().getPayModByTag(MODULE_ID)
        vars["title"] = modPayPal.getTitle()
        vars["url"] = modPayPal.getUrl()
        vars["business"] =  modPayPal.getBusiness()
        return vars

class WPconfirmEPaymentPayPal( conferences.WPConferenceDefaultDisplayBase ):
    #navigationEntry = navigation.NERegistrationFormDisplay

    def __init__(self, rh, conf, reg):
        conferences.WPConferenceDefaultDisplayBase.__init__(self, rh, conf)
        self._registrant=reg


    def _getBody( self, params ):
        wc = WconfirmEPaymentPayPal(self._conf, self._registrant)
        return wc.getHTML()

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._regFormOpt)


class WconfirmEPaymentPayPal( WTemplated ):
    def __init__( self,configuration, registrant):
        self._registrant = registrant
        self._conf = configuration

    def getVars( self ):
        vars = WTemplated.getVars(self)
        vars["message"] = "Thank you for the payment!<br/> You have used PayPal"
        vars["trinfo"]="%s:%s"%(self._registrant.getFirstName(),self._registrant.getSurName())
        return vars

class WPCancelEPaymentPayPal( conferences.WPConferenceDefaultDisplayBase ):
    #navigationEntry = navigation.NERegistrationFormDisplay

    def __init__(self, rh, conf, reg):
        conferences.WPConferenceDefaultDisplayBase.__init__(self, rh, conf)
        self._registrant=reg

    def _getBody( self, params ):
        wc = WCancelEPaymentPayPal( self._conf,self._registrant )
        return wc.getHTML()

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._regFormOpt)

class WCancelEPaymentPayPal( WTemplated ):
    def __init__( self, conference,reg ):
        self._conf = conference
        self._registrant=reg

    def getVars( self ):
        vars = WTemplated.getVars(self)
        vars["message"] = "You have cancelled your transaction.\nPlease check your email in order to complete your PayPal transaction."
        vars["messagedetailPayment"]="%s:%s"%(self._registrant.getFirstName(),self._registrant.getSurName())
        return vars
