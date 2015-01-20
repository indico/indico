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


from MaKaC.plugins.EPayment.skipjack.webinterface import urlHandlers as localUrlHandlers
from MaKaC.plugins.EPayment.skipjack import MODULE_ID



class SkipjackMod( BaseEPayMod ):

    def __init__(self, date=None):
        BaseEPayMod.__init__(self)
        self._title = "skipjack"
        self._url = "https://vpos.skipjack.com/ezPay/order.asp"
        self._description = ""#"Skipjack Registration"
        self._testMode = ""#"100"
        self._textCallBackSuccess = ""
        self._textCallBackCancelled = ""

    def getURL(self):
        try:
           return self._url
        except:
           self._url = ""
           return self._url

    def getId(self):
        return MODULE_ID

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
        self.setDescription(data["description"])
        self.setTextCallBackSuccess(data.get("APResponse", "epayment"))
        self.setTextCallBackCancelled(data.get("CPResponse", "epayment"))

    def getFormHTML(self,prix,Currency,conf,registrant,lang = "en_GB", secure=False):
        """build the registration form to be send to skipjack"""
        url_confirm=localUrlHandlers.UHPayConfirmSkipjack.getURL()
        url_cancel_return=localUrlHandlers.UHPayCancelSkipjack.getURL(registrant)
        url = self._url
        self._conf = registrant.getConference()
        if isinstance(self._url, urlHandlers.URLHandler):
            url = self._url.getURL()


        confId = conf.getId()
        registrantId = registrant.getId()
        s="""<form name="Button" action="%s" method="post" id="%s">
             <input type="hidden" name="skipjack" value="v9RmPSdKf+6q4J93Mz8atwxwFlt1zopZckVx4+uFvIR0Y1dw8/6PcxmfMJwCYGhU1NcMIVp5TlJ5FmaWrECDR5g2AqQ2LgclQt9tCFtnK2S11B+qCpES2H2R0MLXIomO089EIb9HLkN0i0kGLPW2u5b88SD7cibsGXNtYTRRu0RTXmTHyKmkANufwDXlmZ4GjwNmTWTj6W76tikblKyzBw1MEcQ4KEA0OdNsjTIQY4O28/a0PF8bk8jYL03zP5u5gxUdxL9L+K1Gu9ITsXO3U3sjvJC5x2wP/pixl0SZ6SJl+bq50FCnjETicwLkxAgPUTuBgUI8PdzBArlCspDhdQrou++KyORRGbCAuamHfdJ4Hl9cabj7YAugUBPRVt0FhNg+aKv4Y/VgXF626ZMsiC1q9YrP/jMy78DKr5XYpUIJxNMJuDFslzskboAVNF9mdpo1+PuEIiLMKFs9O2q6omel0LqscMOc+96AdRL15iRcraiImHz9VgOUN5slcLOGrwXCr4r2/ksRqD33at26o2Vxgrst4Y0RVafsO70jWZht5Al4hrTFKtktSHIDJ/ypMU8t8qb/JsUzlryLfpWuAhiHHnmJprruoMvvK5NlMI42zQCzhdTIGjWUMrlav6V4X6uPUy6BjtY6ycqbZz9dnw==" />
             <input type="hidden" name="ezPay" value="0pwX0LyFqo/neAMW/8avcxpnQJmlVjudDtdXHa0IFDc=" />
             <input type="hidden" name="creator" value="uPvEbaODYgLAoPjMf0mO7Q==" />
             <input type="hidden" name="UserDefined1" value="%s" />
             <input type="hidden" name="UserDefined2"  value="%s" />
             </form>""" % (url, self.getId(), confId, registrantId)


        return s

    def getUrl(self):
        return self._url

    def setUrl(self,url):
        self._url=url

    def getConfModifEPaymentURL(self, conf):
        return localUrlHandlers.UHConfModifEPaymentSkipjack.getURL(conf)

# Skipjack transaction

class TransactionSkipjack(BaseTransaction):
    """Transaction information which is accessible via Registrant.getTransactionInfo()"""

    def __init__(self,params):
        BaseTransaction.__init__(self)
        self._Data=params

    def getId(self):
        try:
            if self._id:
                pass
        except AttributeError, e:
            self._id="skipjack"
        return self._id

    def getTransactionHTML(self):
        amt = self._Data["szTransactionAmount"]
        amt_dollars = str(int(amt) / 100)
        amt_cents = str(amt)[len(str(amt)) - 2:]
        return"""<table>
                          <tr>
                            <td align="right"><b>Payment with:</b></td>
                            <td align="left">Skipjack</td>
                          </tr>
                          <tr>
                            <td align="right"><b>OrderNumber:</b></td>
                            <td align="left">%s</td>
                          </tr>
                          <tr>
                            <td align="right"><b>Order Total:</b></td>
                            <td align="left">%s.%s</td>
                          </tr>
                          <tr>
                            <td align="right"><b>Name:</b></td>
                            <td align="left">%s</td>
                          </tr>
                  </table>"""%(self._Data["szOrderNumber"],amt_dollars,amt_cents, self._Data["sjname"])

    def getTransactionTxt(self):
        """this is used for notification email """
        #skipjack returns the amount without a decimal point.
        amt = self._Data["szTransactionAmount"]
        amt_dollars = str(int(amt) / 100)
        amt_cents = str(amt)[len(str(amt)) - 2:]
        return"""
\tPayment with:Skipjack\n
\tOrder Number: %s\n
\tOrder Total: %s.%s\n
\tName: %s
"""%(self._Data["szOrderNumber"],amt_dollars,amt_cents, self._Data['sjname'])



def getPayMod():
    return SkipjackMod()

def getPayModClass():
    return SkipjackMod
