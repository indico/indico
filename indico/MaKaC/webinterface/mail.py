# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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

from MaKaC.common.mail import GenericMailer
from MaKaC.webinterface import urlHandlers
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.common import Config
from MaKaC.i18n import _


def getSubjectIndicoTitle():
    minfo=HelperMaKaCInfo.getMaKaCInfoInstance()
    systitle="Indico"
    if minfo.getTitle().strip() != "":
        systitle=minfo.getTitle().strip()
    if minfo.getOrganisation().strip() != "":
        systitle="%s @ %s"%(systitle, minfo.getOrganisation().strip())
    return systitle

class personMail:

    def send(addto, addcc, addfrom, subject, body):
        addto = addto.replace("\r\n","")
        tolist = addto.split(",")
        cclist = addcc.split(",")
        maildata = {
            "fromAddr": addfrom,
            "toList": tolist,
            "ccList": cclist,
            "subject": subject,
            "body": body
            }
        GenericMailer.send(GenericNotification(maildata))
    send = staticmethod( send )


class GenericNotification :

    def __init__(self, data=None):
        if data is None :
            self._fromAddr = ""
            self._toList = []
            self._ccList = []
            self._subject = ""
            self._body = ""
            self._contenttype = "text/plain"
        else :
            self._fromAddr = data.get("fromAddr","")
            self._toList = data.get("toList",[])
            self._ccList = data.get("ccList",[])
            self._subject = data.get("subject","")
            self._body = data.get("body","")
            self._contenttype = data.get("content-type","text/plain")

    def getContentType(self):
        return self._contenttype

    def setContentType(self, contentType):
        self._contenttype = contentType

    def getFromAddr(self):
        return self._fromAddr

    def setFromAddr(self, fromAddr):
        if fromAddr is None :
            return False
        self._fromAddr = fromAddr
        return True

    def getToList(self):
        return self._toList

    def setToList(self, toList):
        if toList is None :
            return False
        self._toList = toList
        return True

    def getCCList(self):
        return self._ccList

    def setCCList(self, ccList):
        if ccList is None :
            return False
        self._ccList = ccList
        return True

    def getSubject(self):
        return self._subject

    def setSubject(self, subject):
        if subject is None :
            return False
        self._subject = subject
        return True

    def getBody(self):
        return self._body

    def setBody(self, body):
        if body is None :
            return False
        self._body = body
        return True


class Mailer:

    def send( notification, fromAddress="" ):
        info = HelperMaKaCInfo.getMaKaCInfoInstance()
        if fromAddress.strip() == "":
            fromAddr = "%s <%s>"%(info.getTitle(), Config.getInstance().getSupportEmail())
        else:
            fromAddr = notification.getFromAddr()
        toAddr = str(notification.getDestination().getEmail())
        text = """%s
--
Indico project <http://indico-software.org/>
                """%(notification.getMsg())
        maildata = {
            "fromAddr": fromAddr,
            "toList": [toAddr],
            "subject": "[Indico] %s" % notification.getSubject(),
            "body": text
            }
        GenericMailer.send(GenericNotification(maildata))
    send = staticmethod( send )


class sendConfirmationRequest:

    def __init__( self, user ):
        self._user = user

    def send( self ):
        text =  _("""Welcome to Indico,
You have created a new account on the Indico conference management system.

In order to activate your new account and being able to be authenticated by the system, please open on your web browser the following URL:

%s?userId=%s&key=%s

Once you've done it, your account will be fully operational so you can log in and start using the system normally.

Thank you for using our system.
                """)%(urlHandlers.UHActiveAccount.getURL(), \
                        self._user.getId(), \
                        self._user.getKey())
        maildata = {
            "fromAddr": "Indico Mailer <%s>" % Config.getInstance().getNoReplyEmail(),
            "toList": [self._user.getEmail()],
            "subject": _("[%s] Confirmation request") % getSubjectIndicoTitle(),
            "body": text
            }
        GenericMailer.send(GenericNotification(maildata))

class sendAccountCreationModeration:

    def __init__( self, user ):
        self._user = user

    def send( self ):
        minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
        name = self._user.getStraightFullName()
        text = """ Dear Administrator,
%s has created a new account in Indico.

In order to activate it, please go to this URL:
<%s>
"""% (name,urlHandlers.UHUserDetails.getURL( self._user ))
        maildata = {
            "fromAddr": "Indico Mailer <%s>" % Config.getInstance().getNoReplyEmail(),
            "toList": minfo.getAdminEmails(),
            "subject": _("[Indico] New account request from %s") % name,
            "body": text
            }
        GenericMailer.send(GenericNotification(maildata))

class sendAccountCreationNotification:

    def __init__( self, user ):
        self._user = user

    def send( self ):
        minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
        name = self._user.getStraightFullName()
        text = """Dear Administrator,
%s has created a new account in Indico.
<%s>
""" % (name,urlHandlers.UHUserDetails.getURL( self._user ))
        maildata = {
            "fromAddr": "Indico Mailer <%s>" % Config.getInstance().getSupportEmail(),
            "toList": minfo.getAdminEmails(),
            "subject": _("[Indico] New account creation"),
            "body": text
            }
        GenericMailer.send(GenericNotification(maildata))

class sendAccountActivated:

    def __init__( self, user ):
        self._user = user

    def send( self ):
        minfo=HelperMaKaCInfo.getMaKaCInfoInstance()
        text =  _("""Welcome to Indico,
Your registration has been accepted by the site administrator.

You can now login using the following username: %s

Thank you for using Indico.
                """)%(self._user.getIdentityList()[0].getLogin())
        maildata = {
            "fromAddr": "Indico Mailer <%s>" % Config.getInstance().getNoReplyEmail(),
            "toList": [self._user.getEmail()],
            "subject": _("[%s] Registration accepted") % getSubjectIndicoTitle(),
            "body": text
            }
        GenericMailer.send(GenericNotification(maildata))

class sendLoginInfo:

    def __init__( self, user ):
        self._user = user

    def send (self ):
        idList = self._user.getIdentityList()
        logins = []
        for id in idList:
            try:
                pw = id.password
            except AttributeError, e:
                pw = _(" Sorry, you are using your NICE credentials to login into Indico. Please contact the CERN helpdesk in case you do not remember your password (helpdesk@cern.ch).")
            logins.append( [id.getAuthenticatorTag(), id.getLogin(),pw])
        if logins == []:
            text = _("Sorry, we did not find your login.\nPlease, create one here:\n%s")%urlHandlers.UHUserDetails.getURL(self._user)
        else:
            text = _("Please, find your login and password:")
            for l in logins:
                text += "\n\n==================\n"
                text += _("system:%s\n")%l[0]
                text += _("Login:%s\n")%l[1]
                text += _("Password:%s\n")%l[2]
                text += "==================\n"
        maildata = {
            "fromAddr": "Indico Mailer <%s>" % Config.getInstance().getNoReplyEmail(),
            "toList": [self._user.getEmail()],
            "subject": _("[%s] Login Information") % getSubjectIndicoTitle(),
            "body": text
            }
        GenericMailer.send(GenericNotification(maildata))
