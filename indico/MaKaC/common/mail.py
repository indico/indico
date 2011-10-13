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
        if skipQueue or not rh:
            cls._send(notification)
        else:
            ContextManager.setdefault('emailQueue', []).append(notification)

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
    def _send(notification):
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
        fromAddr=notification.getFromAddr()
        for to in notification.getToList() :
            if len(to) == 0 :
                notification.getToList().remove(to)
        for cc in notification.getCCList() :
            if len(cc) == 0 :
                notification.getCCList().remove(cc)

        to=", ".join(notification.getToList())
        if not to:
            return
        cc=""
        if len(notification.getCCList())>0:
            cc="Cc: %s\r\n"%", ".join(notification.getCCList())
        try:
            ct=notification.getContentType()
        except:
            ct = "text/plain"
        subject=notification.getSubject()
        body=notification.getBody()
        msg="""Content-Type: %s; charset=\"utf-8\"\r\nFrom: %s\r\nTo: %s\r\n%sSubject: %s\r\n\r\n%s"""%(ct, fromAddr,\
                to,cc,subject,body)
        try:
            Logger.get('mail').info("Mailing %s  CC: %s" % (notification.getToList(), notification.getCCList()))
            server.sendmail(fromAddr,notification.getToList()+notification.getCCList(),msg)
        except smtplib.SMTPRecipientsRefused,e:
            server.quit()
            raise MaKaCError( _("Email address is not valid: ")+str(e.recipients))
        server.quit()

        Logger.get('mail').info('Mail sent to %s' % to)

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