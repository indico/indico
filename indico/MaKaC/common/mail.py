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

from MaKaC.common.logger import Logger

class GenericMailer:

    @staticmethod
    def send(notification):
        server=smtplib.SMTP(Config.getInstance().getSmtpServer())
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
#        raise to
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
            Logger.get('mail').debug("Mailing %s  CC: %s" % (notification.getToList(), notification.getCCList()))
            server.sendmail(fromAddr,notification.getToList()+notification.getCCList(),msg)
        except smtplib.SMTPRecipientsRefused,e:
            server.quit()
            raise MaKaCError( _("Email address is not valid: ")+str(e.recipients))
        server.quit()

        Logger.get('mail').debug('Mail sent to %s' % to)
        
    def sendAndLog(notification, conference, module="", user = None):
        GenericMailer.send(notification)
        logData = {}
        try:
            logData["fromAddr"] = notification._fromAddr
        except:
            logData["fromAddr"] = notification.getFromAddr()
        try:
            logData["toList"] = notification._toList
        except:
            logData["toList"] = notification.getToList()
        logData["ccList"] = notification._ccList 
        try:
            logData["subject"] = notification._subject
        except:
            logData["subject"] = notification.getSubject()
        try:
            logData["body"] = notification._body
        except:
            logData["body"] = notification.getBody()
        conference.getLogHandler().logEmail(logData,module,user)
    sendAndLog = staticmethod(sendAndLog)
