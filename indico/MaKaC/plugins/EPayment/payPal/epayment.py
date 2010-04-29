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

from MaKaC.epayment import BaseEPayMod, BaseTransaction
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.webinterface.common.tools import strip_ml_tags


from MaKaC.plugins.EPayment.payPal.webinterface import urlHandlers as localUrlHandlers

class PayPalMod(BaseEPayMod):

    def __init__(self, data=None):
        BaseEPayMod.__init__(self)
        self._title = "paypal"

        self._url="https://www.paypal.com/cgi-bin/webscr"    
        self._business= ""
          
        if data is not None:
            setValue(data)
        self._id="PayPal"
 
    def getId(self):
        try:
            if self._id:
                pass
        except AttributeError, e:
            self._id="PayPal"
        return self._id

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
          

        
    def getFormHTML(self,prix,Currency,conf,registrant):
        url_return=localUrlHandlers.UHPayConfirmPayPal.getURL(registrant)
        url_cancel_return=localUrlHandlers.UHPayCancelPayPal.getURL(registrant)
        url_notify=localUrlHandlers.UHPayParamsPayPal.getURL(registrant)
        s=""" <form action="%s" method="POST">
                        <input type="hidden" name="cmd" value="_xclick">
                        <input type="hidden" name="business" value="%s">
                        <input type="hidden" name="item_name" value="%s">
                        <input type="hidden" name="amount" value="%s">
                        <INPUT TYPE="hidden" NAME="currency_code" value="%s">
                        <input type="hidden" name="charset" value="windows-1252">
                        <input type="hidden" name="return" value="%s">
                        <input type="hidden" name="cancel_return" value="%s">
                        <input type="hidden" name="notify_url" value="%s">
                        <td align="center"><input type="submit" value="%s" ></td>
                   </form>                           
                       """%(self.getUrl(),self.getBusiness(), "%s: registration for %s"%(registrant.getFullName(),strip_ml_tags(conf.getTitle())),prix,Currency,\
                            url_return,url_cancel_return,url_notify,"Proceed to %s"%self.getTitle())         
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
