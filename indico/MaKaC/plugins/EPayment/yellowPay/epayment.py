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


from MaKaC.plugins.EPayment.yellowPay.webinterface import urlHandlers as localUrlHandlers
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
        self._id="YellowPay"
 
    def getId(self):
        try:
            if self._id:
                pass
        except AttributeError, e:
            self._id="YellowPay"
        return self._id

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

        
    def getFormHTML(self,prix,Currency,conf,registrant):
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
        s=""" <form action="%s" method="POST">
                      <input type="hidden" name="txtShopId" value="%s">
                      <input type="hidden" name="txtLangVersion" value="%s">
                      <input type="hidden" name="txtOrderTotal" value="%s">
                      <input type="hidden" name="txtArtCurrency" value="%s">
                      <input type="hidden" name="txtHash" value="%s">
                      <input type="hidden" name="txtShopPara" value="%s">
                      <td align="center"><input type="submit" value="%s" ></td>
                   </form>                           
                       """%(self.getUrl(),self.getMasterShopID(),"2057",prix,Currency,txtHash,param,"Proceed to %s"%self.getTitle())         
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



