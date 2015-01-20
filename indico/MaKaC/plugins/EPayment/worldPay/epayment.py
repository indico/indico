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

from MaKaC.epayment import BaseEPayMod, BaseTransaction
import MaKaC.webinterface.urlHandlers as urlHandlers


from MaKaC.plugins.EPayment.worldPay.webinterface import urlHandlers as localUrlHandlers
from MaKaC.plugins.EPayment.worldPay import MODULE_ID




class WorldPayMod( BaseEPayMod ):

    def __init__(self, date=None):
        BaseEPayMod.__init__(self)
        self._title = "worldpay"
        self._url = "https://select.worldpay.com/wcc/purchase"
        self._instId = ""#"70950"
        self._description = ""#"EuroPython Registration"
        self._testMode = ""#"100"
        self._textCallBackSuccess = ""
        self._textCallBackCancelled = ""

    def getId(self):
        return MODULE_ID

    def getInstId(self):
        try:
            return self._instId
        except:
            self._instId = ""
        return self._instId

    def setInstId(self, instId):
        self._instId = instId

    def getTextCallBackSuccess(self):
        try:
            return self._textCallBackSuccess
        except:
            self._textCallBackSuccess = ""
        return self._textCallBackSuccess

    def setTextCallBackSuccess(self, txt):
        self._textCallBackSuccess = txt

    def getTextCallBackCancelled(self):
        try:
            return self._textCallBackCancelled
        except:
            self._textCallBackCancelled = ""
        return self._textCallBackCancelled

    def setTextCallBackCancelled(self, txt):
        self._textCallBackCancelled = txt


    def getDescription(self):
        try:
            return self._description
        except:
            self._description = ""
        return self._description

    def setDescription(self, description):
        self._description = description

    def getTestMode(self):
        try:
            return self._testMode
        except:
            self._testMode = ""
        return self._testMode

    def setTestMode(self, testMode):
        self._testMode = testMode


    def setValues(self, data):
        self.setTitle(data.get("title", "epayment"))
        self.setUrl(data.get("url", ""))
        self.setInstId(data["instId"])
        self.setDescription(data["description"])
        self.setTestMode(data["testMode"])
        self.setTextCallBackSuccess(data.get("APResponse", "epayment"))
        self.setTextCallBackCancelled(data.get("CPResponse", "epayment"))

    def getFormHTML(self,prix,Currency,conf,registrant,lang = "en_GB", secure=False):
        """build the registration form to be send to worldPay"""
        url_confirm=localUrlHandlers.UHPayConfirmWorldPay.getURL()
        url_cancel_return=localUrlHandlers.UHPayCancelWorldPay.getURL(registrant)
        url = self._url
        self._conf = registrant.getConference()
        if isinstance(self._url, urlHandlers.URLHandler):
            url = self._url.getURL()
        #raise "%s"%(str(["", registrant.getCountry(), registrant.getPhone(), registrant.getEmail()]))
        s="""<form action="%s" method=POST id="%s">
             <input type=hidden name="instId" value="%s" />
             <input type=hidden name="cartId" value="%s"/>
             <input type=hidden name="amount" value="%s" />
             <input type=hidden name="currency" value="%s" />
             <input type=hidden name="desc" value="%s" />
             <INPUT TYPE=HIDDEN NAME=MC_callback VALUE="%s" />
             <input type=hidden name="M_confId" value="%s">
             <input type=hidden name="M_registrantId" value="%s">
             <input type=hidden name="M_EPaymentName" value="WorldPay">
             <input type=hidden name="M_requestTag" value="confirm">
             <input type=hidden name="testMode" value="%s" />
             <input type=hidden name="name" value="%s %s"/>
             <input type=hidden name="address" value="%s"/>
            <input type=hidden name="postcode" value="%s"/>
            <input type=hidden name="country" value="%s"/>
            <input type=hidden name="tel" value="%s" />
            <input type=hidden name="email" value="%s"/>
            </form>
        """%(url, self.getId(), self._instId, registrant.getId(), "%.2f"%prix, Currency, self._description, url_confirm, self._conf.getId(), registrant.getId(), self._testMode, registrant.getFirstName(),registrant.getSurName(),\
                registrant.getAddress(),"", registrant.getCountry(), registrant.getPhone(), registrant.getEmail())
        return s

    def getUrl(self):
        return self._url

    def setUrl(self,url):
        self._url=url

    def getConfModifEPaymentURL(self, conf):
        return localUrlHandlers.UHConfModifEPaymentWorldPay.getURL(conf)

# World pay transaction

class TransactionWorldPay(BaseTransaction):
    """Transaction information which is accessible via Registrant.getTransactionInfo()"""

    def __init__(self,params):
        BaseTransaction.__init__(self)
        self._Data=params

    def getId(self):
        try:
            if self._id:
                pass
        except AttributeError, e:
            self._id="worldpay"
        return self._id

    def getTransactionHTML(self):
        return"""<table>
                          <tr>
                            <td align="right"><b>Payment with:</b></td>
                            <td align="left">WorldPay</td>
                          </tr>
                          <tr>
                            <td align="right"><b>Payment date:</b></td>
                            <td align="left">%s</td>
                          </tr>
                          <tr>
                            <td align="right"><b>TransactionID:</b></td>
                            <td align="left">%s</td>
                          </tr>
                          <tr>
                            <td align="right"><b>Amount:</b></td>
                            <td align="left">%s %s</td>
                          </tr>
                          <tr>
                            <td align="right"><b>Name:</b></td>
                            <td align="left">%s</td>
                          </tr>
                  </table>"""%(self._Data["payment_date"],self._Data["transId"], self._Data["amount"], \
                             self._Data["currency"], self._Data["name"])

    def getTransactionTxt(self):
        """this is used for notification email """
        return"""
\tPayment with:WorldPay\n
\tPayment Date:%s\n
\tPayment ID:%s\n
\tOrder Total:%s %s\n
\tName n:%s
"""%(self._Data["payment_date"],self._Data["transId"], self._Data["amount"], \
                             self._Data["currency"], self._Data["name"])



def getPayMod():
    return WorldPayMod()

def getPayModClass():
    return WorldPayMod
