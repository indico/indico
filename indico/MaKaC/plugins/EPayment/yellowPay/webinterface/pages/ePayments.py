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

from MaKaC.webinterface.pages import conferences
from MaKaC.webinterface.pages import registrationForm
from MaKaC.webinterface import wcomponents
from xml.sax.saxutils import quoteattr
from indico.core import config as Configuration
from MaKaC.webinterface import urlHandlers
import MaKaC

from MaKaC.plugins.EPayment.yellowPay.webinterface.wcomponents import WTemplated
from MaKaC.plugins.EPayment.yellowPay.webinterface import urlHandlers as localUrlHandlers
from MaKaC.plugins.EPayment.yellowPay import MODULE_ID



class WPConfModifEPaymentYellowPayBase(registrationForm.WPConfModifRegFormBase):

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main", "Main", \
                localUrlHandlers.UHConfModifEPaymentYellowPay.getURL( self._conf ) )
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

class WPConfModifEPaymentYellowPay( WPConfModifEPaymentYellowPayBase ):

    def _getTabContent( self, params ):
        wc = WConfModifEPaymentYellowPay(self._conf)
        p = {
             'dataModificationURL': quoteattr(str(localUrlHandlers.UHConfModifEPaymentYellowPayDataModif.getURL( self._conf )))
            }
        return wc.getHTML(p)

class WConfModifEPaymentYellowPay( WTemplated ):

    def __init__( self, conference ):
        self._conf = conference

    def getVars( self ):
        vars = WTemplated.getVars(self)
        modYellowPay = self._conf.getModPay().getPayModByTag(MODULE_ID)
        vars["title"] = modYellowPay.getTitle()
        vars["url"] = modYellowPay.getUrl()
        vars["shopid"] =  modYellowPay.getShopID()
        vars["mastershopid"] =  modYellowPay.getMasterShopID()
        vars["hashseed"] =  modYellowPay.getHashSeed()
        return vars

class WPConfModifEPaymentYellowPayDataModif( WPConfModifEPaymentYellowPayBase ):

    def _getTabContent( self, params ):
        wc = WConfModifEPaymentYellowPayDataModif(self._conf)
        p = {'postURL': quoteattr(str(localUrlHandlers.UHConfModifEPaymentYellowPayPerformDataModif.getURL( self._conf )))
            }
        return wc.getHTML(p)

class WConfModifEPaymentYellowPayDataModif( WTemplated ):

    def __init__( self, conference ):
        self._conf = conference

    def getVars( self ):
        vars = WTemplated.getVars(self)
        modYellowPay = self._conf.getModPay().getPayModByTag(MODULE_ID)
        vars["title"] = modYellowPay.getTitle()
        vars["url"] = modYellowPay.getUrl()
        vars["shopid"] =  modYellowPay.getShopID()
        vars["mastershopid"] =  modYellowPay.getMasterShopID()
        vars["hashseed"] =  modYellowPay.getHashSeed()
        return vars

class WPconfirmEPaymentYellowPay( conferences.WPConferenceDefaultDisplayBase ):
    #navigationEntry = navigation.NERegistrationFormDisplay

    def __init__(self, rh, conf, reg):
        conferences.WPConferenceDefaultDisplayBase.__init__(self, rh, conf)
        self._registrant=reg


    def _getBody( self, params ):
        wc = WconfirmEPaymentYellowPay(self._conf, self._registrant)
        return wc.getHTML()

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._regFormOpt)


class WconfirmEPaymentYellowPay( WTemplated ):
    def __init__( self,configuration, registrant):
        self._registrant = registrant
        self._conf = configuration

    def getVars( self ):
        vars = WTemplated.getVars(self)
        vars["message"] = "Thank you, your payment has been accepted by Yellowpay"
        vars["trinfo"]="%s:%s"%(self._registrant.getFirstName(),self._registrant.getSurName())
        return vars

class WPCancelEPaymentYellowPay( conferences.WPConferenceDefaultDisplayBase ):
    #navigationEntry = navigation.NERegistrationFormDisplay

    def __init__(self, rh, conf, reg):
        conferences.WPConferenceDefaultDisplayBase.__init__(self, rh, conf)
        self._registrant=reg

    def _getBody( self, params ):
        wc = WCancelEPaymentYellowPay( self._conf,self._registrant )
        return wc.getHTML()

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._regFormOpt)

class WCancelEPaymentYellowPay( WTemplated ):
    def __init__( self, conference,reg ):
        self._conf = conference
        self._registrant=reg

    def getVars( self ):
        vars = WTemplated.getVars(self)
        vars["message"] = "The payment was cancelled (using YellowPay)"
        vars["messagedetailPayment"]="%s:%s"%(self._registrant.getFirstName(),self._registrant.getSurName())
        return vars

class WPNotconfirmEPaymentYellowPay( conferences.WPConferenceDefaultDisplayBase ):
    #navigationEntry = navigation.NERegistrationFormDisplay

    def __init__(self, rh, conf, reg):
        conferences.WPConferenceDefaultDisplayBase.__init__(self, rh, conf)
        self._registrant=reg

    def _getBody( self, params ):
        wc = WNotconfirmEPaymentYellowPay(  self._conf,self._registrant )
        return wc.getHTML()

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._regFormOpt)

class WNotconfirmEPaymentYellowPay( WTemplated ):
    def __init__( self, conference,reg ):
        self._conf = conference
        self._registrant=reg

    def getVars( self ):
        vars = WTemplated.getVars(self)
        vars["message"] = "You have not confirmed!\n (using YellowPay)"
        vars["messagedetailPayment"]="%s:%s"%(self._registrant.getFirstName(),self._registrant.getSurName())
        return vars
