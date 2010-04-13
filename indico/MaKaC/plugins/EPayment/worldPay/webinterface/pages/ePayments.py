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

import MaKaC.webinterface.pages.conferences as conferences
import MaKaC.webinterface.pages.registrationForm as registrationForm
from MaKaC.webinterface import wcomponents
from xml.sax.saxutils import quoteattr
from MaKaC.common import Configuration
from MaKaC.webinterface import urlHandlers
import MaKaC

from MaKaC.plugins.EPayment.worldPay.webinterface.wcomponents import WTemplated
from MaKaC.plugins.EPayment.worldPay.webinterface import urlHandlers as localUrlHandlers





#### configuration interface for WorldPay
class WPConfModifEPaymentWorldPayBase( registrationForm.WPConfModifRegFormBase ):

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main", "Main", \
                localUrlHandlers.UHConfModifEPaymentWorldPay.getURL( self._conf ) )
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
        banner = wcomponents.WEpaymentBannerModif(self._conf.getModPay().getPayModByTag("WorldPay"), self._conf).getHTML()
        html = wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )
        return banner+html

    def _getTabContent( self, params ):
        return "nothing"

class WPConfModifEPaymentWorldPay( WPConfModifEPaymentWorldPayBase ):
    """worldpay settings info page"""
    def _getTabContent( self, params ):
        wc = WConfModifEPaymentWorldPay(self._conf)
        p = {'dataModificationURL': quoteattr(str(localUrlHandlers.UHConfModifEPaymentWorldPayDataModif.getURL( self._conf )))}
        return wc.getHTML(p)


class WConfModifEPaymentWorldPay( WTemplated ):
    def __init__( self, conference):
        self._conf = conference

    def getVars( self ):
        vars = WTemplated.getVars(self)
        modWorldPay = self._conf.getModPay().getPayModByTag("WorldPay")
        vars["title"] = modWorldPay.getTitle()
        vars["url"] = modWorldPay.getUrl()
        vars["instId"] =  modWorldPay.getInstId()
        vars["description"] = modWorldPay.getDescription()
        vars["testMode"] = modWorldPay.getTestMode()
        vars["APResponse"] = quoteattr(modWorldPay.getTextCallBackSuccess())
        vars["CPResponse"] = quoteattr(modWorldPay.getTextCallBackCancelled())
        return vars


class WPConfModifEPaymentWorldPayDataModif( WPConfModifEPaymentWorldPayBase):
    """world pay configuration page """
    def _getTabContent( self, params ):
        wc = WConfModifEPaymentWorldPayDataModif(self._conf)
        p = {'postURL': quoteattr(str(localUrlHandlers.UHConfModifEPaymentWorldPayPerformDataModif.getURL( self._conf )))}
        return wc.getHTML(p)

class WConfModifEPaymentWorldPayDataModif( WTemplated ):
    
    def __init__( self, conference ):
        self._conf = conference

    def getVars( self ):
        vars = WTemplated.getVars(self)
        modWorldPay = self._conf.getModPay().getPayModByTag("WorldPay")
        vars["title"] = modWorldPay.getTitle()
        vars["url"] = modWorldPay.getUrl()
        vars["instId"] =  modWorldPay.getInstId()
        vars["description"] = modWorldPay.getDescription()
        vars["testMode"] = modWorldPay.getTestMode()
        vars["APResponse"] = modWorldPay.getTextCallBackSuccess()
        vars["CPResponse"] = modWorldPay.getTextCallBackCancelled()
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

<u>WorldPay data:</u>
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





class WEPaymentWorldPayModifFrame( WTemplated ):
    
    def __init__(self, conf, aw):
        self._conf = conf
        self._aw = aw
        self._worldPay = self._conf.getModPay().getPayModByTag("WorldPay")
    
    def getHTML( self, body, **params ):
        params["body"] = body
        return WTemplated.getHTML( self, params )
    
    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["context"] = wcomponents.WConfModifHeader( self._conf, self._aw ).getHTML(vars)
        vars["title"] = self._worldPay.getTitle()
        vars["titleTabPixels"] = self.getTitleTabPixels()
        vars["intermediateVTabPixels"] = self.getIntermediateVTabPixels()
        vars["closeHeaderTags"] = self.getCloseHeaderTags()
        return vars

    def getOwnerComponent( self ):
        wc = wcomponents.WConferenceModifFrame(self._conf, self._aw)
        return wc
        
    def getIntermediateVTabPixels( self ):
        wc = self.getOwnerComponent()
        return 7 + wc.getIntermediateVTabPixels()
        
    def getTitleTabPixels( self ):
        wc = self.getOwnerComponent()
        return wc.getTitleTabPixels() - 7
    
    def getCloseHeaderTags( self ):
        wc = self.getOwnerComponent()
        return "</table></td></tr>" + wc.getCloseHeaderTags()

### classes needed by callback
class WPConfirmEPaymentWorldPay( conferences.WPConferenceDefaultDisplayBase ):
    """Confirmation page for Worldpay callback """

    def __init__( self, rh, conf, reg ):
        conferences.WPConferenceDefaultDisplayBase.__init__(self, rh, conf)
        self._registrant = reg
        
    def _getBody( self, params ):
        wc = WConfirmEPaymentWorldPay( self._conf, self._registrant)
        
    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defindeSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._regFormOpt)


class WconfirmEPaymentWorldPay( WTemplated ):
    def __init__( self,configuration, registrant):
        self._registrant = registrant
        self._conf = configuration
        
    def getVars( self ):
        vars = WTemplated.getVars(self)
        vars["message"] = "Thank you to the payment!\n you have used WorldPay"
        vars["trinfo"]="%s:%s"%(self._registrant.getFirstName(),self._registrant.getSurName())
        return vars

class WPEPaymentWorldPayAccepted(conferences.WPConferenceDefaultDisplayBase):
    def __init__(self, rh, conf, reg ):
        conferences.WPConferenceDefaultDisplayBase.__init__(self, rh, conf)
        self._registrant = reg
    
    def display(self, params):
        modPay = self._conf.getModPay()
        return modPay.getPayModByTag("WorldPay").getTextCallBackSuccess()%params

class WPEPaymentWorldPayCancelled(conferences.WPConferenceDefaultDisplayBase):
    def __init__(self, rh, conf, reg ):
        conferences.WPConferenceDefaultDisplayBase.__init__(self, rh, conf)
        self._registrant = reg
    
    def display(self, params):
        modPay = self._conf.getModPay()
        return modPay.getPayModByTag("WorldPay").getTextCallBackCancelled()%params

class WPCancelEPaymentWorldPay( conferences.WPConferenceDefaultDisplayBase ):

    def __init__(self, rh, conf, reg):
        conferences.WPConferenceDefaultDisplayBase.__init__(self, rh, conf)
        self._registrant=reg
        
    def _getBody( self, params ):
        wc = WCancelEPaymentWorldPay( self._conf,self._registrant )
        return wc.getHTML()

    def _defineSectionMenu( self ): 
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._regFormOpt)    
        
class WCancelEPaymentWorldPay( WTemplated ):
    def __init__( self, conference,reg ):
        self._conf = conference
        self._registrant=reg

    def getVars( self ):
        vars = WTemplated.getVars(self)
        vars["message"] = "You have Cancelled!\nplease check your mail\n you have used WorldPay"
        vars["messagedetailPayment"]="%s:%s"%(self._registrant.getFirstName(),self._registrant.getSurName())
        return vars 