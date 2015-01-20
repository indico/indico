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
from MaKaC.webinterface.common.tools import strip_ml_tags


from MaKaC.plugins.EPayment.payPal.webinterface import urlHandlers as localUrlHandlers
from MaKaC.plugins.EPayment.payPal import MODULE_ID

class PayPalMod(BaseEPayMod):

    def __init__(self, data=None):
        BaseEPayMod.__init__(self)
        self._title = "paypal"

        self._url="https://www.paypal.com/cgi-bin/webscr"
        self._business= ""

        if data is not None:
            setValue(data)

    def getId(self):
        return MODULE_ID

    def clone(self, newSessions):
        sesf = PayPalMod()
        sesf.setTitle(self.getTitle())
        sesf.setUrl(self.getUrl())
        sesf.setBusiness(self.getBusiness())

        return sesf

    def setValues(self, data):
        self.setTitle(data.get("title", "epayment"))
        self.setUrl(data.get("url", ""))
        self.setBusiness(data["business"])

    def getUrl(self):
        return self._url
    def setUrl(self,url):
        self._url=url

    def getBusiness(self):
        return self._business
    def setBusiness(self,business):
        self._business= business

    def getFormHTML(self,prix,Currency,conf,registrant,lang = "en_GB", secure=False):
        url_return=localUrlHandlers.UHPayConfirmPayPal.getURL(registrant)
        url_cancel_return=localUrlHandlers.UHPayCancelPayPal.getURL(registrant)
        url_notify=localUrlHandlers.UHPayParamsPayPal.getURL(registrant)
        s=""" <form action="%s" method="POST" id="%s">
                        <input type="hidden" name="cmd" value="_xclick">
                        <input type="hidden" name="business" value="%s">
                        <input type="hidden" name="item_name" value="%s">
                        <input type="hidden" name="amount" value="%s">
                        <INPUT TYPE="hidden" NAME="currency_code" value="%s">
                        <input type="hidden" name="charset" value="utf-8">
                        <input type="hidden" name="return" value="%s">
                        <input type="hidden" name="cancel_return" value="%s">
                        <input type="hidden" name="notify_url" value="%s">
                   </form>
                       """%(self.getUrl(),self.getId(),self.getBusiness(), "%s: registration for %s"%(registrant.getFullName(),strip_ml_tags(conf.getTitle())),prix,Currency,\
                            url_return,url_cancel_return,url_notify)
        #s=cgi.escape(s)
        return s

    def getConfModifEPaymentURL(self, conf):
        return localUrlHandlers.UHConfModifEPaymentPayPal.getURL(conf)



class TransactionPayPal(BaseTransaction):

    def __init__(self,parms):
        BaseTransaction.__init__(self)
        self._Data=parms


    def getId(self):
        try:
            if self._id:
                pass
        except AttributeError, e:
            self._id="paypal"
        return self._id

    def getTransactionHTML(self):
        return"""<table>
                          <tr>
                            <td align="right"><b>Payment with:</b></td>
                            <td align="left">PayPal</td>
                          </tr>
                          <tr>
                            <td align="right"><b>Payment Date:</b></td>
                            <td align="left">%s</td>
                          </tr>
                          <tr>
                            <td align="right"><b>Payment ID:</b></td>
                            <td align="left">%s</td>
                          </tr>
                          <tr>
                            <td align="right"><b>Order Total:</b></td>
                            <td align="left">%s %s</td>
                          </tr>
                          <tr>
                            <td align="right"><b>verify sign:</b></td>
                            <td align="left">%s</td>
                          </tr>
                        </table>"""%(self._Data["payment_date"],self._Data["payer_id"], self._Data["mc_gross"], \
                             self._Data["mc_currency"], self._Data["verify_sign"])
    def getTransactionTxt(self):
        return"""
\tPayment with:PayPal\n
\tPayment Date:%s\n
\tPayment ID:%s\n
\tOrder Total:%s %s\n
\tverify sign:%s
"""%(self._Data["payment_date"],self._Data["payer_id"], self._Data["mc_gross"], \
                             self._Data["mc_currency"], self._Data["verify_sign"])



def getPayMod():
    return PayPalMod()

def getPayModClass():
    return PayPalMod
