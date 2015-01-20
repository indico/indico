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
from MaKaC.webinterface import urlHandlers


from MaKaC.plugins.EPayment.yellowPay.webinterface import urlHandlers as localUrlHandlers
from MaKaC.plugins.EPayment.yellowPay import MODULE_ID
import md5

class YellowPayMod(BaseEPayMod):

    def __init__(self, data=None):
        BaseEPayMod.__init__(self)
        self._title = "YellowPay"

        self._url="https://yellowpay.postfinance.ch/checkout/Yellowpay.aspx?userctrl=Invisible"
        self._shopID= ""
        self._masterShopID  = ""
        self._hashSeed = ""
        if data is not None:
            setValue(data)

    def getId(self):
        return MODULE_ID

    def clone(self, newSessions):
        sesf = YellowPayMod()
        sesf.setTitle(self.getTitle())
        sesf.setUrl(self.getUrl())
        sesf.setShopID(self.getShopID())
        sesf.setMasterShopID(self.getMasterShopID())
        sesf.setHashSeed(self.getHashSeed())
        sesf.setEnabled(self.isEnabled())

        return sesf

    def setValues(self, data):
        self.setTitle(data.get("title", "epayment"))
        self.setUrl(data.get("url", ""))
        self.setShopID(data.get("shopid", ""))
        self.setMasterShopID(data.get("mastershopid", ""))
        self.setHashSeed(data.get("hashseed", ""))

    def getUrl(self):
        return self._url
    def setUrl(self,url):
        self._url=url

    def getShopID(self):
        return self._shopID
    def setShopID(self,shopID):
        self._shopID= shopID

    def getMasterShopID(self):
        return self._masterShopID
    def setMasterShopID(self,masterShopID):
        self._masterShopID  = masterShopID

    def getHashSeed(self):
        return self._hashSeed
    def setHashSeed(self,hashSeed):
        self._hashSeed  =  hashSeed


    def getFormHTML(self,prix,Currency,conf,registrant,lang = "en_GB", secure=False):
        l=[]
        l.append("%s=%s"%("confId",conf.getId()))
        l.append("%s=%s"%("registrantId",registrant.getId()))
        param= "&".join( l )
        #Shop-ID + txtArtCurrency + txtOrderTotal + Hash seed
        m=md5.new()
        m.update(self.getShopID())
        m.update(Currency)

        m.update("%.2f"%prix)
        m.update(self.getHashSeed())
        #txtHash =  cgi.escape(m.digest(),True)
        txtHash =m.hexdigest()
        s=""" <form action="%s" method="POST" id="%s">
                      <input type="hidden" name="txtShopId" value="%s">
                      <input type="hidden" name="txtLangVersion" value="%s">
                      <input type="hidden" name="txtOrderTotal" value="%s">
                      <input type="hidden" name="txtArtCurrency" value="%s">
                      <input type="hidden" name="txtHash" value="%s">
                      <input type="hidden" name="txtShopPara" value="%s">
                   </form>
                       """%(self.getUrl(),self.getId(), self.getMasterShopID(),"2057",prix,Currency,txtHash,param)
        #s=cgi.escape(s)
        return s

    def getConfModifEPaymentURL(self, conf):
        return localUrlHandlers.UHConfModifEPaymentYellowPay.getURL(conf)

class TransactionYellowPay(BaseTransaction):

    def __init__(self,parms):
        BaseTransaction.__init__(self)
        self._Data=parms


    def getId(self):
        try:
            if self._id:
                pass
        except AttributeError, e:
            self._id="yellowpay"
        return self._id

    def getTransactionHTML(self):

        textOption="""
                          <tr>
                            <td align="right"><b>ESR Member:</b></td>
                            <td align="left">%s</td>
                          </tr>
                          <tr>
                            <td align="right"><b>ESR Ref:</b></td>
                            <td align="left">%s</td>
                          </tr>
         """%(self._Data["ESR_Member"],self._Data["ESR_Ref"])
        return"""<table>
                          <tr>
                            <td align="right"><b>Payment with:</b></td>
                            <td align="left">YellowPay</td>
                          </tr>
                          <tr>
                            <td align="right"><b>Payment Date:</b></td>
                            <td align="left">%s</td>
                          </tr>
                          <tr>
                            <td align="right"><b>TransactionID:</b></td>
                            <td align="left">%s</td>
                          </tr>
                          <tr>
                            <td align="right"><b>Order Total:</b></td>
                            <td align="left">%s %s</td>
                          </tr>
                          <tr>
                            <td align="right"><b>PayMet:</b></td>
                            <td align="left">%s</td>
                          </tr>
                          %s
                        </table>"""%(self._Data["payment_date"],self._Data["TransactionID"], self._Data["OrderTotal"], \
                             self._Data["Currency"], self._Data["PayMet"],textOption)
    def getTransactionTxt(self):
        textOption="""
\tESR Member:%s\n
\tESR Ref:%s\n
"""%(self._Data["ESR_Member"],self._Data["ESR_Ref"])
        return"""
\tPayment with:YellowPay\n
\tPayment Date:%s\n
\tTransactionID:%s\n
\tOrder Total:%s %s\n
\tPayMet:%s
%s
"""%(self._Data["payment_date"],self._Data["TransactionID"], self._Data["OrderTotal"], \
                             self._Data["Currency"], self._Data["PayMet"],textOption)


def getPayMod():
    return YellowPayMod()

def getPayModClass():
    return YellowPayMod



