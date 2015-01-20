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

from MaKaC.plugins.EPayment.skipjack.webinterface.wcomponents import WTemplated
from MaKaC.plugins.EPayment.skipjack.webinterface import urlHandlers as localUrlHandlers
from MaKaC.plugins.EPayment.skipjack import MODULE_ID


#### configuration interface for Skipjack
class WPConfModifEPaymentSkipjackBase( registrationForm.WPConfModifRegFormBase ):

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main", "Main", \
                localUrlHandlers.UHConfModifEPaymentSkipjack.getURL( self._conf ) )
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

class WPConfModifEPaymentSkipjack( WPConfModifEPaymentSkipjackBase ):
    """skipjacksettings info page"""
    def _getTabContent( self, params ):
        wc = WConfModifEPaymentSkipjack(self._conf)
        p = {'dataModificationURL': quoteattr(str(localUrlHandlers.UHConfModifEPaymentSkipjackDataModif.getURL( self._conf )))}
        return wc.getHTML(p)


class WConfModifEPaymentSkipjack( WTemplated ):

    def __init__( self, conference):
        self._conf = conference

    def getVars( self ):
        vars = WTemplated.getVars(self)
        modSkipjack = self._conf.getModPay().getPayModByTag(MODULE_ID)
        vars["title"] = modSkipjack.getTitle()
        vars["url"] = modSkipjack.getUrl()
        vars["description"] = modSkipjack.getDescription()
        vars["testMode"] = modSkipjack.getTestMode()
        vars["APResponse"] = quoteattr(modSkipjack.getTextCallBackSuccess())
        vars["CPResponse"] = quoteattr(modSkipjack.getTextCallBackCancelled())
        return vars


class WPConfModifEPaymentSkipjackDataModif( WPConfModifEPaymentSkipjackBase):
    """skipjack configuration page """
    def _getTabContent( self, params ):
        wc = WConfModifEPaymentSkipjackDataModif(self._conf)
        p = {'postURL': quoteattr(str(localUrlHandlers.UHConfModifEPaymentSkipjackPerformDataModif.getURL( self._conf )))}
        #blowing chunks in here...
        return wc.getHTML(p)

class WConfModifEPaymentSkipjackDataModif( WTemplated ):

    def __init__( self, conference ):
        self._conf = conference

    def getVars( self ):
        vars = WTemplated.getVars(self)
        modSkipjack = self._conf.getModPay().getPayModByTag(MODULE_ID)
        vars["title"] = modSkipjack.getTitle()
        vars["url"] = modSkipjack.getUrl()
        vars["description"] = modSkipjack.getDescription()
        vars["testMode"] = modSkipjack.getTestMode()
        vars["APResponse"] = modSkipjack.getTextCallBackSuccess()
        vars["CPResponse"] = modSkipjack.getTextCallBackCancelled()
        vars["legend"] = """<u>Registrant data:</u>
%(registrantTitle)s : Registrant title
%(registrantFirstName)s : Registrant first name
%(registrantSurName)s : Registrant surname
%(registrantInstitution)s : Registrant institution
%(registrantAddress)s : Registrant address
%(registrantCity)s : Registrant city
%(registrantCountry)s : Registrant country
%(registrantPhone)s : Registrant phone
%(registrantFax)s : Registrant fax
%(registrantEmail)s : Registrant email
%(registrantPersonalHomepage)s : Registrant personnal homepage
%(payment_date)s : Date of payment

<u>Skipjack data:</u>
%(postcode)s            %(email)s
%(transId)s             %(compName)s
%(transStatus)s         %(countryMatch)s
%(authMode)s            %(amount)s
%(AVS)s                 %(authCost)s
%(country)s             %(lang)s
%(cartId)s              %(name)s
%(transTime)s           %(desc)s
%(authAmount)s          %(rawAuthCode)s
%(authAmountString)s    %(address)s
%(amountString)s        %(cardType)s
%(currency)s            %(cost)s
%(rawAuthMessage)s      %(countryString)s
%(authCurrency)s"""
        return vars

### classes needed by callback
class WPConfirmEPaymentSkipjack( conferences.WPConferenceDefaultDisplayBase ):
    """Confirmation page for Skipjack callback """

    def __init__( self, rh, conf, reg ):
        conferences.WPConferenceDefaultDisplayBase.__init__(self, rh, conf)
        self._registrant = reg

    def _getBody( self, params ):
        wc = WConfirmEPaymentSkipjack( self._conf, self._registrant)

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defindeSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._regFormOpt)


class WconfirmEPaymentSkipjack( WTemplated ):
    def __init__( self,configuration, registrant):
        self._registrant = registrant
        self._conf = configuration

    def getVars( self ):
        vars = WTemplated.getVars(self)
        vars["urlDisplay"] = localUrlHandlers.UHPayDisplayInfoSkipjack.getURL(self._registrant)
        return vars

class WPEPaymentSkipjackAccepted(conferences.WPConferenceDefaultDisplayBase):
    def __init__(self, rh, conf, reg ):
        conferences.WPConferenceDefaultDisplayBase.__init__(self, rh, conf)
        self._registrant = reg

    def _getBody( self, params ):
        wc = WconfirmEPaymentSkipjack(self._conf, self._registrant)
        #Uncomment this line and comment above if the redirect method at sj changes.
        #wc = WdisplayPaymentInfo(self._conf, self._registrant)
        return wc.getHTML()

class WdisplayPaymentInfo( WTemplated ):
    def __init__( self,configuration, registrant):
        self._registrant = registrant
        self._conf = configuration

    def getVars( self ):
        vars = WTemplated.getVars(self)
        vars["message"] = "Thank you, your payment has been accepted by Skipjack."
        vars["trinfo"]=self._registrant.getTransactionInfo().getTransactionHTML()
        #vars["trinfo"]="%s:%s"%(self._registrant.getFirstName(),self._registrant.getSurName())
        return vars

class WPEPaymentSkipjackDisplayInfo(conferences.WPConferenceDefaultDisplayBase):
    def __init__(self, rh, conf, reg ):
        conferences.WPConferenceDefaultDisplayBase.__init__(self, rh, conf)
        self._registrant = reg

    def _getBody( self, params ):
        wc = WdisplayPaymentInfo(self._conf, self._registrant)
        return wc.getHTML()

class WPEPaymentSkipjackCancelled(conferences.WPConferenceDefaultDisplayBase):
    def __init__(self, rh, conf, reg, denyMsg):
        conferences.WPConferenceDefaultDisplayBase.__init__(self, rh, conf)
        self._registrant = reg
        self._denyMsg = denyMsg

    def _getBody( self, params ):
        wc = WCancelEPaymentSkipjack(self._conf, self._registrant, self._denyMsg)
        return wc.getHTML()


class WPCancelEPaymentSkipjack( conferences.WPConferenceDefaultDisplayBase ):

    def __init__(self, rh, conf, reg):
        conferences.WPConferenceDefaultDisplayBase.__init__(self, rh, conf)
        self._registrant=reg

    def _getBody( self, params ):
        wc = WCancelEPaymentSkipjack( self._conf,self._registrant )
        return wc.getHTML()

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._regFormOpt)

class WCancelEPaymentSkipjack( WTemplated ):
    def __init__( self, conference,reg, denyMsg ):
        self._conf = conference
        self._registrant=reg
        self._denyMsg=denyMsg

    def getVars( self ):
        vars = WTemplated.getVars(self)
        vars["message"] = "The payment was denied by Skipjack because \"%s\". Verify the credit card information you entered was correct." % self._denyMsg
        vars["messagedetailPayment"]="Registrant Name:%s %s"%(self._registrant.getFirstName(),self._registrant.getSurName())
        return vars
