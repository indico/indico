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
import uuid

from MaKaC.common.cache import GenericCache
from MaKaC.common.mail import GenericMailer
from MaKaC.webinterface import urlHandlers
from MaKaC.common.info import HelperMaKaCInfo
from indico.core.config import Config
from MaKaC.i18n import _

from indico.web.flask.util import url_for


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
        if data is None:
            self._fromAddr = ""
            self._toList = []
            self._ccList = []
            self._bccList = []
            self._subject = ""
            self._body = ""
            self._contenttype = "text/plain"
            self._attachments = []
        else:
            self._fromAddr = data.get("fromAddr", "")
            self._toList = data.get("toList", [])
            self._ccList = data.get("ccList", [])
            self._bccList = data.get("bccList", [])
            self._subject = data.get("subject", "")
            self._body = data.get("body", "")
            self._contenttype = data.get("content-type", "text/plain")
            self._attachments = data.get("attachments", [])

    def getAttachments(self):
        return self._attachments

    def addAttachment(self, attachment):
        """
        Attachment is a dictionary with two keys:
        - name: containing the filename of the file
        - binary: containing the file data
        """

        self._attachments.append(attachment)

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

    def setBCCList(self, bccList):
        if bccList is None :
            return False
        self._bccList = bccList
        return True

    def getBCCList(self):
        return self._bccList

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

    def __init__(self, user, conf=None):
        self._user = user
        self._conf = conf

    def send( self ):
        url = urlHandlers.UHConfActiveAccount.getURL(self._conf) if self._conf else urlHandlers.UHActiveAccount.getURL()
        text =  _("""Welcome to Indico,
You have created a new account on the Indico conference management system.

In order to activate your new account and being able to be authenticated by the system, please open on your web browser the following URL:

%s?userId=%s&key=%s

Once you've done it, your account will be fully operational so you can log in and start using the system normally.

Thank you for using our system.
                """)%(url,
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

class sendAccountDisabled:

    def __init__( self, user ):
        self._user = user

    def send( self ):
        text =  _("""Dear user,
Your account has been disabled by the site administrator.
                """)
        maildata = { "fromAddr": "Indico Mailer<%s>"%Config.getInstance().getNoReplyEmail(), "toList": [self._user.getEmail()], "subject": _("[%s] Account disabled")%getSubjectIndicoTitle(), "body": text }
        GenericMailer.send(GenericNotification(maildata))


def send_login_info(user, event=None):
    token_storage = GenericCache('resetpass')
    endpoint = 'event.confLogin-resetPassword' if event else 'user.signIn-resetPassword'

    idList = user.getIdentityList()
    logins = []
    for id in idList:
        if not hasattr(id, 'setPassword'):
            config = Config.getInstance()
            extra_message = config.getAuthenticatorConfigById(id.getAuthenticatorTag()).get("ResetPasswordMessage")
            msg = _("Sorry, you are using an externally managed account (%s) to login into Indico.") % id.getLogin()
            if extra_message:
                msg += "\n" + extra_message
            logins.append({
                'tag': id.getAuthenticatorTag(),
                'login': id.getLogin(),
                'error': msg
            })
        else:
            tag = id.getAuthenticatorTag()
            login = id.getLogin()
            data = {'tag': tag, 'login': login}
            token = str(uuid.uuid4())
            while token_storage.get(token):
                token = str(uuid.uuid4())
            token_storage.set(token, data, 6*3600)
            url = url_for(endpoint, event, token=token, _external=True, _secure=True)
            logins.append({
                'tag': tag,
                'login': login,
                'link': url
            })
    if not logins:
        url = urlHandlers.UHUserDetails.getURL(user)
        text = _("Sorry, we did not find your login.\nPlease, create one here:\n%s") % url
    else:
        text = _("You can use the following links within the next six hours to reset your password.")
        for entry in logins:
            text += "\n\n==================\n"
            if 'link' in entry:
                text += _("Click below to reset your password for the %s login '%s':\n") % (entry['tag'],
                                                                                            entry['login'])
                text += entry['link']
            else:
                text += entry['error']
            text += "\n==================\n"
    maildata = {
        "fromAddr": "Indico Mailer <%s>" % Config.getInstance().getNoReplyEmail(),
        "toList": [user.getEmail()],
        "subject": _("[%s] Login Information") % getSubjectIndicoTitle(),
        "body": text
    }
    GenericMailer.send(GenericNotification(maildata))
