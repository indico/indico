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


from persistent import Persistent
from MaKaC.common.Locators import Locator
from MaKaC.trashCan import TrashCanManager
from MaKaC.plugins import PluginLoader
from MaKaC.errors import MaKaCError, FormValuesError
import re


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
            self.payMods[mod.__name__] = mod.epayment.getPayMod()
        self._p_changed = 1
        if initSorted:
            self.initSortedModPay()

    def updatePlugins(self, initSorted=True):
        epaymentModules = PluginLoader.getPluginsByType("EPayment")
        changed = False
        for mod in epaymentModules:
            name = mod.MODULE_ID
            if name not in self.payMods:
                self.payMods[name] = mod.epayment.getPayMod()
                changed = True
            else:
                # this seems to be some kind of replacement mechanism
                # no idea of its use though...
                if not isinstance(self.payMods[name],
                                  mod.epayment.getPayModClass()):
                    newMod = mod.epayment.getPayMod()
                    self.payMods[mod.MODULE_ID] = newMod
                    changed = True

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

    def getPaymentReceiptMsg(self):
        try:
            return self.receiptMsg
        except:
            self.receiptMsg = EPaymentDefaultValues.getDefaultReceiptMsg()
        return self.receiptMsg

    def setPaymentReceiptMsg(self, txt):
        self.receiptMsg = txt

    def getPaymentSuccessMsg(self):
        try:
            return self.successMsg
        except:
            self.successMsg = EPaymentDefaultValues.getDefaultSuccessMsg()
        return self.successMsg

    def setPaymentSuccessMsg(self, txt):
        self.successMsg = txt

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
        self.updatePlugins()
        return self._sortedModPay

    def getSortedEnabledModPay(self):
        smp = self.getSortedModPay()
        l = []
        for m in smp:
            if m.isEnabled():
                l.append(m)
        return l

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

    @staticmethod
    def getDefaultSuccessMsg():
        return """Congratulations, your payment was successful."""

    @staticmethod
    def getDefaultReceiptMsg():
        return """Please, see the summary of your order:"""

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

    def getFormHTML(self, price, currency, registrant, lang = "en_GB", secure=False):
        """
        Returns the html form that will be used to send the information to the epayment server.
        """
        raise Exception("This method must be overloaded")

    def getOnSelectedHTML(self):
        return """function (amount) {
                     $('#paySubmit').removeAttr('disabled');
                     $('#totalAmount').text(amount);
                     $('#inPlaceSelectPaymentMethod').hide();
                }"""

    def getConfModifEPaymentURL(self, conf):
        """
        For each plugin there is just one URL for all requests. The plugin will have its own parameters to manage different URLs (have a look to urlHandler.py). This method returns that general URL.
        """
        raise Exception("This method must be overloaded")

    def setValues(self, data):
        """ Saves the values coming in a dict (data) in the corresping class variables. (e.g. title, url, business, etc) """
        raise Exception("This method must be overloaded")

    def getPluginSectionHTML(self, conf, aw, urlStatus, urlModif, img, text):
        selbox = ""
        return """
                <tr>
                <td>
                    <a href=%s><img src="%s" alt="%s" class="imglink"></a>&nbsp;%s&nbsp;<a href=%s>%s</a>
                </td>
                </tr>
                """%(str(urlStatus), img, text, selbox, str(urlModif), self.getTitle())


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


class PaymentMethod(Persistent):

    def __init__(self, conf, name="", displayName="", type="", extraFee=0.0):
        self._name = name
        self._displayName = displayName
        self._type = type
        self._extraFee = extraFee
        self._conf = conf

    def getName(self):
        return self._name

    def setName(self, name):
        self._name = name

    def getDisplayName(self):
        return self._displayName

    def setDisplayName(self, displayName):
        self._displayName = displayName

    def getType(self):
        return self._type

    def setType(self, type):
        self._type = type

    def getExtraFee(self):
        return self._extraFee

    def setExtraFee(self, extraFee):
        match = re.compile(r'^(\d+(?:[\.]\d+)?)$').match(extraFee)
        if match:
            extraFee = match.group(1)
        else:
            raise FormValuesError( _('The extra fee format is in incorrect. The fee must be a number: 999.99'))
        self._extraFee = extraFee

    def getConference(self):
        return self._conf

    def setConference(self, conf):
        self._conf = conf

    def getLocator(self):
        if self.getConference() == None:
            return Locator()
        lconf = self.getConference().getLocator()
        lconf["paymentMethodName"] = self.getName()
        return lconf
