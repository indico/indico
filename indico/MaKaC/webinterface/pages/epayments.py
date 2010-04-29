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
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.navigation as navigation
import string
from MaKaC import epayment
from MaKaC.webinterface import wcomponents
from xml.sax.saxutils import quoteattr
from MaKaC.common import Configuration
from datetime import timedelta,datetime
from MaKaC.webinterface.common.countries import CountryHolder
import MaKaC.webinterface.pages.registrationForm as registrationForm
from MaKaC.conference import Session
from MaKaC.i18n import _
from MaKaC.common import HelperMaKaCInfo
# ----------------- MANAGEMENT AREA ---------------------------
class WPConfModifEPaymentBase( registrationForm.WPConfModifRegFormBase ):
    
    def _setActiveTab( self ):
        self._tabEPay.setActive()
        
class WPConfModifEPayment( WPConfModifEPaymentBase ):
    
    def _getTabContent( self, params ):
        wc = WConfModifEPayment(self._conf, self._getAW().getUser())
        return wc.getHTML()

class WConfModifEPayment( wcomponents.WTemplated ):
    
    def __init__( self, conference, user ):
        self._conf = conference
        self._user = user

    def _getSectionsHTML(self):
        modPay=self._conf.getModPay()
        html=[]
        enabledBulb = Configuration.Config.getInstance().getSystemIconURL( "enabledSection" )
        notEnabledBulb = Configuration.Config.getInstance().getSystemIconURL( "disabledSection" )
        enabledText = _("Click to disable")
        disabledText = _("Click to enable")
        for gs in modPay.getSortedModPay():
                      
            urlStatus = urlHandlers.UHConfModifEPaymentEnableSection.getURL(self._conf)
            urlStatus.addParam("epayment", gs.getId())
            urlModif = gs.getConfModifEPaymentURL(self._conf)
            img = enabledBulb
            text = enabledText
            if not gs.isEnabled():
                img = notEnabledBulb
                text = disabledText

            # CERN Plugin: Just admins can see and modify it
            if gs.getId() == "CERNYellowPay":
                minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
                al = minfo.getAdminList()
                if not al.isAdmin( self._user ):
                    from MaKaC.plugins.EPayment.CERNYellowPay.options import globalOptions
                    endis="enable"
                    departmentName = globalOptions[1][1]["defaultValue"]
                    emailAddress = globalOptions[0][1]["defaultValue"]
                    if gs.isEnabled():
                        endis="disable"
                        emailAddress = minfo.getSupportEmail()
                        departmentName = "Indico support"
                    html.insert(0, """
                        <tr>
                        <td>
                            <img src=%s alt="%s" class="imglink">&nbsp;&nbsp;<b>CERN E-Payment</b> <small>
                            (please, contact <a href="mailto:%s?subject=Indico Epayment - Conference ID: %s">%s</a> to %s 
                            the CERN e-payment module)</small>
                        </td>
                        </tr>
                        """%(img, text, emailAddress, self._conf.getId(), departmentName, endis))
                    continue
            #################################################
            
            selbox = ""
            html.append("""
                        <tr>
                        <td>
                            <a href=%s><img src=%s alt="%s" class="imglink"></a>&nbsp;%s&nbsp;<a href=%s>%s</a>
                        </td>
                        </tr>
                        """%(quoteattr(str(urlStatus)), img, text, selbox, quoteattr(str(urlModif)), gs.getTitle()) )
        html.insert(0, """<a href="" name="sections"></a><input type="hidden" name="oldpos"><table align="left">""")
        html.append("</table>")
        return "".join(html)


    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        modPay=self._conf.getModPay()
        vars["setStatusURL"]=urlHandlers.UHConfModifEPaymentChangeStatus.getURL(self._conf)
        vars["enablePic"]=quoteattr(str(Configuration.Config.getInstance().getSystemIconURL( "enabledSection" )))
        vars["disablePic"]=quoteattr(str(Configuration.Config.getInstance().getSystemIconURL( "disabledSection" )))
        if modPay.isActivated():
            vars["changeTo"] = "False"
            vars["status"] = _("ENABLED")
            vars["changeStatus"] = _("DISABLE")
            vars["disabled"] = ""   
            vars["detailPayment"] = self._conf.getModPay().getPaymentDetails()
            vars["conditionsPayment"] = self._conf.getModPay().getPaymentConditions()
            vars["specificConditionsPayment"] = self._conf.getModPay().getPaymentSpecificConditions()
            vars["conditionsEnabled"] = "DISABLED"
            if self._conf.getModPay().arePaymentConditionsEnabled():
                vars["conditionsEnabled"] = "ENABLED"
        else:
            vars["changeTo"] = "True"
            vars["status"] = _("DISABLED")
            vars["changeStatus"] = _("ENABLE") 
            vars["disabled"] = "disabled"
            vars["detailPayment"] = ""
            vars["conditionsPayment"] = ""
            vars["conditionsEnabled"] = "DISABLED"
            vars["specificConditionsPayment"] = ""
        vars["dataModificationURL"]=urlHandlers.UHConfModifEPaymentdetailPaymentModification.getURL(self._conf)
        vars["sections"] = self._getSectionsHTML()
        return vars

class WPConfModifEPaymentDataModification( WPConfModifEPaymentBase ):
    
    def _getTabContent( self, params ):
        wc = WConfModifEPaymentDataModification(self._conf)
        return wc.getHTML()

class WConfModifEPaymentDataModification( wcomponents.WTemplated ):
    
    def __init__( self, conference ):
        self._conf = conference

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["postURL"]=urlHandlers.UHConfModifEPaymentPerformdetailPaymentModification.getURL(self._conf)
        vars["detailPayment"]= self._conf.getModPay().getPaymentDetails()
        vars["conditionsPayment"]= self._conf.getModPay().getPaymentConditions()
        vars["specificConditionsPayment"]= self._conf.getModPay().getPaymentSpecificConditions()
        vars["conditionsEnabled"]= ""
        if self._conf.getModPay().arePaymentConditionsEnabled():
            vars["conditionsEnabled"]= "checked=\"checked\""
        return vars    
        
