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

import smtplib
from MaKaC.common import Config
from MaKaC.errors import MaKaCError
from MaKaC.i18n import _

from MaKaC.common.logger import Logger
from MaKaC.common.contextManager import ContextManager

class GenericMailer:

    @classmethod
    def send(cls, notification, skipQueue=False):
        if isinstance(notification, dict):
            # Wrap a raw dictionary in a notification class
            from MaKaC.webinterface.mail import GenericNotification
            notification = GenericNotification(notification)
        # enqueue emails if we have a rh and do not skip queuing, otherwise send immediately
        rh = ContextManager.get('currentRH', None)
        mailData = cls._prepare(notification)

        if mailData:
            if skipQueue or not rh:
                cls._send(mailData)
            else:
                ContextManager.setdefault('emailQueue', []).append(mailData)

    @classmethod
    def flushQueue(cls, send):
        queue = ContextManager.get('emailQueue', None)
        if not queue:
            return
        if send:
            # send all emails
            for mail in queue:
                cls._send(mail)
        # clear the queue no matter if emails were sent or not
        del queue[:]

    @staticmethod
    def _prepare(notification):
        fromAddr=notification.getFromAddr()
        for to in notification.getToList() :
            if len(to) == 0 :
                notification.getToList().remove(to)
        for cc in notification.getCCList() :
            if len(cc) == 0 :
                notification.getCCList().remove(cc)

        to=", ".join(notification.getToList())
        cc=""
        if len(notification.getCCList())>0:
            cc="Cc: %s\r\n"%", ".join(notification.getCCList())
        if not to and not cc:
            return

        try:
            ct=notification.getContentType()
        except:
            ct = "text/plain"
        subject=notification.getSubject()
        body=notification.getBody()
        msg="""Content-Type: %s; charset=\"utf-8\"\r\nFrom: %s\r\nTo: %s\r\n%sSubject: %s\r\n\r\n%s"""%(ct, fromAddr,\
                to,cc,subject,body)
        toList = notification.getToList()
        ccList = notification.getCCList()
        return {
            'msg': msg,
            'toList': toList,
            'ccList': ccList,
            'fromAddr': fromAddr,
            'to': to
        }

    @staticmethod
    def _send(msgData):
        server=smtplib.SMTP(*Config.getInstance().getSmtpServer())
        if Config.getInstance().getSmtpUseTLS():
            server.ehlo()
            (code, errormsg) = server.starttls()
            if code != 220:
                raise MaKaCError( _("Can't start secure connection to SMTP server: %d, %s")%(code, errormsg))
        if Config.getInstance().getSmtpLogin():
            login = Config.getInstance().getSmtpLogin()
            password = Config.getInstance().getSmtpPassword()
            (code, errormsg) = server.login(login, password)
            if code != 235:
                raise MaKaCError( _("Can't login on SMTP server: %d, %s")%(code, errormsg))

        try:
            Logger.get('mail').info("Mailing %s  CC: %s" % (msgData['toList'], msgData['ccList']))
            server.sendmail(msgData['fromAddr'], msgData['toList'] + msgData['ccList'], msgData['msg'])
        except smtplib.SMTPRecipientsRefused,e:
            server.quit()
            raise MaKaCError("Email address is not valid: %s" % e.recipients)
        server.quit()
        Logger.get('mail').info('Mail sent to %s' % msgData['to'])

    @classmethod
    def _log(cls, data):
        data['conference'].getLogHandler().logEmail(data['data'], data['module'], data['user'])

    @classmethod
    def sendAndLog(cls, notification, conference, module='', user=None, skipQueue=False):
        cls.send(notification, skipQueue=skipQueue)
        logData = {
            'fromAddr': notification.getFromAddr(),
            'toList': notification.getToList(),
            'ccList': notification.getCCList(),
            'subject': notification.getSubject(),
            'body': notification.getBody()
        }
        conference.getLogHandler().logEmail(logData, module, user)
