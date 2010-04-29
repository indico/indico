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


from persistent import Persistent
from MaKaC.common.Locators import Locator
from MaKaC.trashCan import TrashCanManager
from MaKaC.plugins.pluginLoader import PluginLoader

class EPayment(Persistent):

    def __init__(self, conf, groupData=None):
        self._conf = conf
        if groupData is None:
            self.activated = False

        else:
            self.activated = groupData.get("activated", False)
        self.paymentDetails = ""
        self.paymentConditionsEnabled = False
        self.paymentConditions = EPaymentDefaultValues.getDefaultConditions()
        self.paymentSpecificConditions = ""
        self.payMods = {}
        self.enableSendEmailPaymentDetails=True

    def loadPlugins(self, initSorted=True):
        self.payMods = {}
        epaymentModules = PluginLoader.getPluginsByType("EPayment")
        for mod in epaymentModules:
            try:
                self.payMods[mod.pluginName] = mod.epayment.getPayMod()
            except:
                pass
        self._p_changed = 1
        #self.payMods["PayLater"] = PayLaterMod()
        if initSorted:
            self.initSortedModPay()

##        #Simple-SubForms
##        self.yellowPay = YellowPayMod()
##        self.payLater = PayLaterMod()
##        self.payPal = PayPalMod()
##        self.worldPay = WorldPayMod()
##        #All SortedForms

    def updatePlugins(self, initSorted=True):
        epaymentModules = PluginLoader.getPluginsByType("EPayment")
        changed = False
        for mod in epaymentModules:
            try:
                if not mod.pluginName in self.payMods.keys():
                    print "add mod %s"%mod
                    self.payMods[mod.pluginName] = mod.epayment.getPayMod()
                    print "%s"%self.payMods
                    changed = True
                else:
                    if not isinstance(self.payMods[mod.pluginName], mod.epayment.getPayModClass()):
                        #oldMod = self.payMods[mod.pluginName]
                        print "replace by mod %s"%mod
                        newMod = mod.epayment.getPayMod()
                        self.payMods[mod.pluginName] = newMod
                        changed = True
            except:
                pass
        if changed:
            self._p_changed = 1
        if initSorted:
            self.initSortedModPay()


    def initSortedModPay(self):
        try:
            self.payMods.values()
        except:
            self.loadPlugins(initSorted=False)
        self.updatePlugins(initSorted=False)
        self._sortedModPay = self.payMods.values()
        self._p_changed = 1

    def getPayModByTag(self, tag):
        try:
            if not self.payMods.keys():
                self.loadPlugins()
        except:
            self.loadPlugins()
        if tag in self.payMods.keys():
            return self.payMods[tag]
        self.updatePlugins()
        if tag in self.payMods.keys():
            return self.payMods[tag]
        return None

    def getConference(self):
        return self._conf
    getOwner = getConference

    def setConference(self, conf):
        self._conf = conf
    setOwner = setConference

    def getPaymentDetails(self):
        try:
            return self.paymentDetails
        except:
            self.paymentDetails = ""
        return self.paymentDetails

    def setPaymentDetails(self, txt):
        self.paymentDetails = txt

    def getPaymentSpecificConditions(self):
        try:
            return self.specificPaymentConditions
        except:
            self.specificPaymentConditions = ""
        return self.specificPaymentConditions

    def setPaymentSpecificConditions(self, txt):
        self.specificPaymentConditions = txt

    def getPaymentConditions(self):
        try:
            return self.paymentConditions
        except:
            self.paymentConditions = EPaymentDefaultValues.getDefaultConditions()
        return self.paymentConditions

    def setPaymentConditions(self, txt):
        self.paymentConditions = txt

    def arePaymentConditionsEnabled(self):
        try:
            if self.paymentConditionsEnabled:
                pass
        except Exception,e:
            self.paymentConditionsEnabled = False
        return self.paymentConditionsEnabled

    def setPaymentConditionsEnabled(self,v):
        self.paymentConditionsEnabled=v

    def hasPaymentConditions(self):
        if self.arePaymentConditionsEnabled():
            return True
        elif self.getPaymentSpecificConditions().strip()!="":
            return True
        return False

    def getConditions(self):
        if self.arePaymentConditionsEnabled() and self.getPaymentSpecificConditions().strip() == "":
            return "%s"%(self.getPaymentConditions())
        else:
            return "%s"%(self.getPaymentSpecificConditions())

    def isActivated(self):
        return self.activated

    def activate(self):
        self.activated = True

    def deactivate(self):
        self.activated = False

    def setActivated(self, value):
        self.activated = value

    def isMandatoryAccount(self):
        try:
            if self._mandatoryAccount:
                pass
        except AttributeError, e:
            self._mandatoryAccount = True
        return self._mandatoryAccount

    def setMandatoryAccount(self, v=True):
        self._mandatoryAccount = v

    def setTitle( self, newName ):
        self.title = newName.strip()

    def getTitle( self ):
        return self.title

    def isEnableSendEmailPaymentDetails(self):
        try:
            if self.enableSendEmailPaymentDetails:
                pass
        except AttributeError, e:
            self.enableSendEmailPaymentDetails=True
        return self.enableSendEmailPaymentDetails

    def setEnableSendEmailPaymentDetails(self, v=True):
        self.enableSendEmailPaymentDetails = v

##    def getModPayPal(self):
##        return self.payPal
##
##    def getModYellowPay(self):
##        try:
##            return self.yellowPay
##        except:
##            self.yellowPay = YellowPayMod()
##        return self.yellowPay
##
##    def getModPayLater(self):
##        try:
##            return self.payLater
##        except:
##            self.payPal = PayPalMod()
##        return self.payLater
##
##    def getModWorldPay(self):
##        try:
##            return self.worldPay
##        except:
##            self.worldPay = WorldPayMod()
##        return self.worldPay

    def getSortedModPay(self):
##        try:
##            if self._sortedModPay:
##                pass
##        except AttributeError,e:
##            self.initSortedModPay()
        self.updatePlugins()
        return self._sortedModPay

    def addToSortedModPay(self, form, i=None):
        if i is None:
            i=len(self.getSortedModPay())
        try:
            self.getSortedModPay().remove(form)
        except ValueError,e:
            pass
        self.getSortedModPay().insert(i, form)
        self.notifyModification()
        return True

    def removeFromSortedModPay(self, form):
        try:
            self.getSortedModPay().remove(form)
        except ValueError,e:
            return False
        self.notifyModification()
        return True

    def getModPayById(self, id):
        return self.getPayModByTag(id)
##        if id == "yellowpay":
##            return self.getModYellowPay()
##        if id == "paylater":
##            return self.getModPayLater()
##        if id == "paypal":
##            return self.getModPayPal()
##        if id == "worldPay":
##            return self.getModWorldPay()
##        return None


    def getLocator( self ):
        """Gives back (Locator) a globaly unique identification encapsulated in
            a Locator object for the RegistrationForm instance """
        if self.getConference() == None:
            return Locator()
        lconf = self.getConference().getLocator()
        return lconf


    def recover(self):
        TrashCanManager().remove(self)

    def notifyModification(self):
        self._p_changed=1
        self._conf.notifyModification()

class EPaymentDefaultValues:

    @staticmethod
    def getDefaultConditions():
        return """
CANCELLATION :

All refunds requests must be in writing by mail to the Conference Secretary as soon as possible.
The Conference committee reserves the right to refuse reimbursement of part or all of the fee in the case of late cancellation. However, each case of cancellation would be considered individually.
"""

class BaseEPayMod(Persistent):

    def __init__(self):
        self._enabled = False
        self._title = ""
        self._id = ""

    def getId(self):
        return self._id

    def getTitle(self):
        return self._title

    def setTitle(self, title):
        self._title = title

    def setEnabled(self, v):
        self._enabled = v

    def isEnabled(self):
        try:
            if self._enabled:
                pass
        except AttributeError, e:
            self._enabled = False
        return self._enabled

    def getFormHTML(self,prix,Currency):
        """
        Returns the html form that will be used to send the information to the epayment server.
        """
        raise Exception("This method must be overloaded")

    def getConfModifEPaymentURL(self, conf):
        """
        For each plugin there is just one URL for all requests. The plugin will have its own parameters to manage different URLs (have a look to urlHandler.py). This method returns that general URL.
        """
        raise Exception("This method must be overloaded")

    def setValues(self, data):
        """ Saves the values coming in a dict (data) in the corresping class variables. (e.g. title, url, business, etc) """
        raise Exception("This method must be overloaded")

##class YellowPayMod(BaseEPayMod):
##
##    def __init__(self, data=None):
##        BaseEPayMod.__init__(self)
##        self._title = "yellowpay"
##
##        self._url="https://yellowpay.postfinance.ch/checkout/Yellowpay.aspx?userctrl=Invisible"
##        self._shopID= ""
##        self._masterShopID  = ""
##        self._hashSeed = ""
##        if data is not None:
##            setValue(data)
##        self._id="yellowpay"
##
##    def getId(self):
##        try:
##            if self._id:
##                pass
##        except AttributeError, e:
##            self._id="yellowpay"
##        return self._id
##
##    def clone(self, newSessions):
##        sesf = YellowPayMod()
##        sesf.setTitle(self.getTitle())
##        sesf.setUrl(self.getUrl())
##        sesf.setShopID(self.getShopID())
##        sesf.setMasterShopID(self.getMasterShopID())
##        sesf.setHashSeed(self.getHashSeed())
##        sesf.setEnabled(self.isEnabled())
##
##        return sesf
##
##    def setValues(self, data):
##        self.setTitle(data.get("title", "epayment"))
##        self.setUrl(data.get("url", ""))
##        self.setShopID(data.get("shopid", ""))
##        self.setMasterShopID(data.get("mastershopid", ""))
##        self.setHashSeed(data.get("hashseed", ""))
##
##    def getTitle(self):
##        return self._title
##    def setTitle(self, title):
##        self._title = title
##
##    def getUrl(self):
##        return self._url
##    def setUrl(self,url):
##        self._url=url
##
##    def getShopID(self):
##        return self._shopID
##    def setShopID(self,shopID):
##        self._shopID= shopID
##
##    def getMasterShopID(self):
##        return self._masterShopID
##    def setMasterShopID(self,masterShopID):
##        self._masterShopID  = masterShopID
##
##    def getHashSeed(self):
##        return self._hashSeed
##    def setHashSeed(self,hashSeed):
##        self._hashSeed  =  hashSeed
##
##
##    def getFormHTML(self,prix,Currency,conf,registrant):
##        l=[]
##        l.append("%s=%s"%("confId",conf.getId()))
##        l.append("%s=%s"%("registrantId",registrant.getId()))
##        param= "&".join( l )
##        #Shop-ID + txtArtCurrency + txtOrderTotal + Hash seed
##        m=md5.new()
##        m.update(self.getShopID())
##        m.update(Currency)
##
##        m.update("%f"%prix)
##        m.update(self.getHashSeed())
##        #txtHash =  cgi.escape(m.digest(),True)
##        txtHash =m.hexdigest()
##        s=""" <form action="%s" method="POST">
##                      <input type="hidden" name="txtShopId" value="%s">
##                      <input type="hidden" name="txtLangVersion" value="%s">
##                      <input type="hidden" name="txtOrderTotal" value="%s">
##                      <input type="hidden" name="txtArtCurrency" value="%s">
##                      <input type="hidden" name="txtHash" value="%s">
##                      <input type="hidden" name="txtShopPara" value="%s">
##                      <td align="center"><input type="submit" value="%s" ></td>
##                   </form>
##                       """%(self.getUrl(),self.getMasterShopID(),"2057",prix,Currency,txtHash,param,"submit")
##        #s=cgi.escape(s)
##        return s

class BaseTransaction(Persistent):

    def __init__(self):
        pass

    def getId(self):
        return""

    def getTransactionHTML(self):
        return ""

    def getTransactionHTMLModif(self):
        return ""

    def isChangeable(self):
        return False

##class TransactionYellowPay(BaseTransaction):
##
##    def __init__(self,parms):
##        BaseTransaction.__init__(self)
##        self._Data=parms
##
##
##    def getId(self):
##        try:
##            if self._id:
##                pass
##        except AttributeError, e:
##            self._id="yellowpay"
##        return self._id
##
##    def getTransactionHTML(self):
##
##        textOption="""
##                          <tr>
##                            <td align="right"><b>ESR Member:</b></td>
##                            <td align="left">%s</td>
##                          </tr>
##                          <tr>
##                            <td align="right"><b>ESR Ref:</b></td>
##                            <td align="left">%s</td>
##                          </tr>
##         """%(self._Data["ESR_Member"],self._Data["ESR_Ref"])
##        return"""<table>
##                          <tr>
##                            <td align="right"><b>Payment with:</b></td>
##                            <td align="left">YellowPay</td>
##                          </tr>
##                          <tr>
##                            <td align="right"><b>Payment Date:</b></td>
##                            <td align="left">%s</td>
##                          </tr>
##                          <tr>
##                            <td align="right"><b>TransactionID:</b></td>
##                            <td align="left">%s</td>
##                          </tr>
##                          <tr>
##                            <td align="right"><b>Order Total:</b></td>
##                            <td align="left">%s %s</td>
##                          </tr>
##                          <tr>
##                            <td align="right"><b>PayMet:</b></td>
##                            <td align="left">%s</td>
##                          </tr>
##                          %s
##                        </table>"""%(self._Data["payment_date"],self._Data["TransactionID"], self._Data["OrderTotal"], \
##                             self._Data["Currency"], self._Data["PayMet"],textOption)
##    def getTransactionTxt(self):
##        textOption="""
##\tESR Member:%s\n
##\tESR Ref:%s\n
##"""%(self._Data["ESR_Member"],self._Data["ESR_Ref"])
##        return"""
##\tPayment with:YellowPay\n
##\tPayment Date:%s\n
##\tTransactionID:%s\n
##\tOrder Total:%s %s\n
##\tPayMet:%s
##%s
##"""%(self._Data["payment_date"],self._Data["TransactionID"], self._Data["OrderTotal"], \
##                             self._Data["Currency"], self._Data["PayMet"],textOption)

class PayLaterMod(BaseEPayMod):

    def __init__(self, data=None):
        BaseEPayMod.__init__(self)
        self._title = "pay later"
        self._detailPayment= ""
        if data is not None:
            setValue(data) #TODO: check this, it will fail
        self._id="paylater"

    def getId(self):
        try:
            if self._id:
                pass
        except AttributeError, e:
            self._id="paylater"
        return self._id

    def clone(self, newSessions):
        sesf = PayLaterMod()
        sesf.setTitle(self.getTitle())


        return sesf

    def setValues(self, data):
        self.setTitle(data.get("title", "epayment"))
        self.setdetailPayment(data.get("detailPayment", ""))

    def getdetailPayment(self):
        return self._detailPayment
    def setdetailPayment(self, detailPayment):
        self._detailPayment= detailPayment

    def getTitle(self):
        return self._title
    def setTitle(self, title):
        self._title = title


class TransactionPayLaterMod(BaseTransaction):

    def __init__(self,parms):
        BaseTransaction.__init__(self)
        self._Data=parms

    def isChangeable(self): return True

    def getId(self):
        try:
            if self._id:
                pass
        except AttributeError, e:
            self._id="paylater"
        return self._id

    def getTransactionHTML(self):

        return"""<table>
                          <tr>
                            <td align="right"><b>Payment with:</b></td>
                            <td align="left">Pay later</td>
                          </tr>
                          <tr>
                            <td align="right"><b>OrderTotal:</b></td>
                            <td align="left">%s %s</td>
                          </tr>
                        </table>"""%(self._Data["OrderTotal"], \
                             self._Data["Currency"])




##class PayPalMod(BaseEPayMod):
##
##    def __init__(self, data=None):
##        BaseEPayMod.__init__(self)
##        self._title = "paypal"
##
##        self._url="https://www.paypal.com/cgi-bin/webscr"
##        self._business= ""
##
##        if data is not None:
##            setValue(data)
##        self._id="paypal"
##
##    def getId(self):
##        try:
##            if self._id:
##                pass
##        except AttributeError, e:
##            self._id="paypal"
##        return self._id
##
##    def clone(self, newSessions):
##        sesf = PayPalMod()
##        sesf.setTitle(self.getTitle())
##        sesf.setUrl(self.getUrl())
##        sesf.setBusiness(self.getBusiness())
##
##        return sesf
##
##    def setValues(self, data):
##        self.setTitle(data.get("title", "epayment"))
##        self.setUrl(data.get("url", ""))
##        self.setBusiness(data["business"])
##
##    def getTitle(self):
##        return self._title
##    def setTitle(self, title):
##        self._title = title
##
##    def getUrl(self):
##        return self._url
##    def setUrl(self,url):
##        self._url=url
##
##    def getBusiness(self):
##        return self._business
##    def setBusiness(self,business):
##        self._business= business
##
##
##
##    def getFormHTML(self,prix,Currency,conf,registrant):
##        url_return=urlHandlers.UHPayConfirmPayPal.getURL(registrant)
##        url_cancel_return=urlHandlers.UHPayCancelPayPal.getURL(registrant)
##        url_notify=urlHandlers.UHPayParamsPayPal.getURL(registrant)
##        s=""" <form action="%s" method="POST">
##                        <input type="hidden" name="cmd" value="_xclick">
##                        <input type="hidden" name="business" value="%s">
##                        <input type="hidden" name="amount" value="%s">
##                        <INPUT TYPE="hidden" NAME="currency_code" value="%s">
##                        <input type="hidden" name="charset" value="windows-1252">
##                        <input type="hidden" name="return" value="%s">
##                        <input type="hidden" name="cancel_return" value="%s">
##                        <input type="hidden" name="notify_url" value="%s">
##                        <td align="center"><input type="submit" value="%s" ></td>
##                   </form>
##                       """%(self.getUrl(),self.getBusiness(),prix,Currency,\
##                            url_return,url_cancel_return,url_notify,"submit")
##        #s=cgi.escape(s)
##        return s
##class TransactionPayPal(BaseTransaction):
##
##    def __init__(self,parms):
##        BaseTransaction.__init__(self)
##        self._Data=parms
##
##
##    def getId(self):
##        try:
##            if self._id:
##                pass
##        except AttributeError, e:
##            self._id="paypal"
##        return self._id
##
##    def getTransactionHTML(self):
##        return"""<table>
##                          <tr>
##                            <td align="right"><b>Payment with:</b></td>
##                            <td align="left">PayPal</td>
##                          </tr>
##                          <tr>
##                            <td align="right"><b>Payment Date:</b></td>
##                            <td align="left">%s</td>
##                          </tr>
##                          <tr>
##                            <td align="right"><b>Payment ID:</b></td>
##                            <td align="left">%s</td>
##                          </tr>
##                          <tr>
##                            <td align="right"><b>Order Total:</b></td>
##                            <td align="left">%s %s</td>
##                          </tr>
##                          <tr>
##                            <td align="right"><b>verify sign:</b></td>
##                            <td align="left">%s</td>
##                          </tr>
##                        </table>"""%(self._Data["payment_date"],self._Data["payer_id"], self._Data["mc_gross"], \
##                             self._Data["mc_currency"], self._Data["verify_sign"])
##    def getTransactionTxt(self):
##        return"""
##\tPayment with:PayPal\n
##\tPayment Date:%s\n
##\tPayment ID:%s\n
##\tOrder Total:%s %s\n
##\tverify sign:%s
##"""%(self._Data["payment_date"],self._Data["payer_id"], self._Data["mc_gross"], \
##                             self._Data["mc_currency"], self._Data["verify_sign"])
##
### WorldPay module
##class WorldPayMod( BaseEPayMod ):
##
##    def __init__(self, date=None):
##        BaseEPayMod.__init__(self)
##        self._title = "worldpay"
##        self._id = "worldpay"
##        self._url = "https://select.worldpay.com/wcc/purchase"
##        self._instId = ""#"70950"
##        self._description = ""#"EuroPython Registration"
##        self._testMode = ""#"100"
##        self._textCallBackSuccess = ""
##        self._textCallBackCancelled = ""
##
##    def getId(self):
##        try:
##            if self._id:
##                pass
##        except AttributeError, e:
##            self._id="worldpay"
##        return self._id
##
##    def getInstId(self):
##        try:
##            return self._instId
##        except:
##            self._instId = ""
##        return self._instId
##
##    def setInstId(self, instId):
##        self._instId = instId
##
##    def getTextCallBackSuccess(self):
##        try:
##            return self._textCallBackSuccess
##        except:
##            self._textCallBackSuccess = ""
##        return self._textCallBackSuccess
##
##    def setTextCallBackSuccess(self, txt):
##        self._textCallBackSuccess = txt
##
##    def getTextCallBackCancelled(self):
##        try:
##            return self._textCallBackCancelled
##        except:
##            self._textCallBackCancelled = ""
##        return self._textCallBackCancelled
##
##    def setTextCallBackCancelled(self, txt):
##        self._textCallBackCancelled = txt
##
##
##    def getDescription(self):
##        try:
##            return self._description
##        except:
##            self._description = ""
##        return self._description
##
##    def setDescription(self, description):
##        self._description = description
##
##    def getTestMode(self):
##        try:
##            return self._testMode
##        except:
##            self._testMode = ""
##        return self._testMode
##
##    def setTestMode(self, testMode):
##        self._testMode = testMode
##
##
##    def setValues(self, data):
##        self.setTitle(data.get("title", "epayment"))
##        self.setUrl(data.get("url", ""))
##        self.setInstId(data["instId"])
##        self.setDescription(data["description"])
##        self.setTestMode(data["testMode"])
##        self.setTextCallBackSuccess(data.get("APResponse", "epayment"))
##        self.setTextCallBackCancelled(data.get("CPResponse", "epayment"))
##
##    def getFormHTML(self,prix,Currency,conf,registrant):
##        """build the registration form to be send to worldPay"""
##        url_confirm=urlHandlers.UHPayConfirmWorldPay.getURL()
##        url_cancel_return=urlHandlers.UHPayCancelWorldPay.getURL(registrant)
##        url = self._url
##        self._conf = registrant.getConference()
##        if isinstance(self._url, urlHandlers.URLHandler):
##            url = self._url.getURL()
##        #raise "%s"%(str(["", registrant.getCountry(), registrant.getPhone(), registrant.getEmail()]))
##        s="""<form action="%s" method=POST>
##             <input type=submit value="proceed to WorldPay"/>
##             <input type=hidden name="instId" value="%s" />
##             <input type=hidden name="cartId" value="%s"/>
##             <input type=hidden name="amount" value="%s" />
##             <input type=hidden name="currency" value="%s" />
##             <input type=hidden name="desc" value="%s" />
##             <INPUT TYPE=HIDDEN NAME=MC_callback VALUE="%s" />
##             <input type=hidden name="M_confId" value="%s">
##             <input type=hidden name="M_registrantId" value="%s">
##             <input type=hidden name="testMode" value="%s" />
##             <input type=hidden name="name" value="%s %s"/>
##             <input type=hidden name="address" value="%s"/>
##            <input type=hidden name="postcode" value="%s"/>
##            <input type=hidden name="country" value="%s"/>
##            <input type=hidden name="tel" value="%s" />
##            <input type=hidden name="email" value="%s"/>
##            </form>
##        """%(url, self._instId, registrant.getId(), "%.2f"%prix, Currency, self._description, url_confirm, self._conf.getId(), registrant.getId(), self._testMode, registrant.getFirstName(),registrant.getSurName(),\
##                registrant.getAddress(),"", registrant.getCountry(), registrant.getPhone(), registrant.getEmail())
##        return s
##
##    def getTitle(self):
##        return self._title
##    def setTitle(self, title):
##        self._title = title
##
##    def getUrl(self):
##        return self._url
##
##    def setUrl(self,url):
##        self._url=url
##
### World pay transaction
##
##class TransactionWorldPay(BaseTransaction):
##    """Transaction information which is accessible via Registrant.getTransactionInfo()"""
##
##    def __init__(self,params):
##        BaseTransaction.__init__(self)
##        self._Data=params
##
##    def getId(self):
##        try:
##            if self._id:
##                pass
##        except AttributeError, e:
##            self._id="worldpay"
##        return self._id
##
##    def getTransactionHTML(self):
##        return"""<table>
##                          <tr>
##                            <td align="right"><b>Payment with:</b></td>
##                            <td align="left">WorldPay</td>
##                          </tr>
##                          <tr>
##                            <td align="right"><b>Payment date:</b></td>
##                            <td align="left">%s</td>
##                          </tr>
##                          <tr>
##                            <td align="right"><b>TransactionID:</b></td>
##                            <td align="left">%s</td>
##                          </tr>
##                          <tr>
##                            <td align="right"><b>Amount:</b></td>
##                            <td align="left">%s %s</td>
##                          </tr>
##                          <tr>
##                            <td align="right"><b>Name:</b></td>
##                            <td align="left">%s</td>
##                          </tr>
##                  </table>"""%(self._Data["payment_date"],self._Data["transId"], self._Data["amount"], \
##                             self._Data["currency"], self._Data["name"])
##
##    def getTransactionTxt(self):
##        """this is used for notification email """
##        return"""
##\tPayment with:WorldPay\n
##\tPayment Date:%s\n
##\tPayment ID:%s\n
##\tOrder Total:%s %s\n
##\tName n:%s
##"""%(self._Data["payment_date"],self._Data["transId"], self._Data["amount"], \
##                             self._Data["currency"], self._Data["name"])
