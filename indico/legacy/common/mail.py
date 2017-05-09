# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

import smtplib
from email import charset
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import g

from indico.core.config import Config
from indico.core.logger import Logger
from indico.legacy.errors import MaKaCError
from indico.util.event import unify_event_args
from indico.util.i18n import _
from indico.util.string import to_unicode

# Prevent base64 encoding of utf-8 e-mails
charset.add_charset('utf-8', charset.SHORTEST)


class GenericMailer:

    @classmethod
    def send(cls, notification, skipQueue=False):
        if isinstance(notification, dict):
            # Wrap a raw dictionary in a notification class
            from indico.legacy.webinterface.mail import GenericNotification
            notification = GenericNotification(notification)
        # enqueue emails if we have a rh and do not skip queuing, otherwise send immediately
        rh = g.get('rh')
        mailData = cls._prepare(notification)

        if mailData:
            if skipQueue or not rh:
                cls._send(mailData)
            else:
                g.setdefault('email_queue', []).append(mailData)

    @classmethod
    def has_queue(cls):
        return bool(g.get('email_queue'))

    @classmethod
    def flushQueue(cls, send):
        queue = g.get('email_queue', None)
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
        fromAddr = notification.getFromAddr()
        replyAddr = getattr(notification, '_replyAddr', None)
        toList = set(filter(None, notification.getToList()))
        ccList = set(filter(None, notification.getCCList()))
        if hasattr(notification, "getBCCList"):
            bccList = set(notification.getBCCList())
        else:
            bccList = set()

        msg = MIMEMultipart()
        msg["Subject"] = to_unicode(notification.getSubject()).strip()
        msg["From"] = fromAddr
        msg["To"] = ', '.join(toList) if toList else 'Undisclosed-recipients:;'
        if ccList:
            msg["Cc"] = ', '.join(ccList)
        if replyAddr:
            msg['Reply-to'] = replyAddr

        if not toList and not ccList and not bccList:
            return

        try:
            ct = notification.getContentType()
        except Exception:
            ct = "text/plain"

        body = notification.getBody()
        if ct == "text/plain":
            part1 = MIMEText(body, "plain", "utf-8")
        elif ct == "text/html":
            part1 = MIMEText(body, "html", "utf-8")
        else:
            raise MaKaCError(_("Unknown MIME type: %s") % (ct))
        msg.attach(part1)

        if hasattr(notification, 'getAttachments'):
            attachments = notification.getAttachments() or []
            for attachment in attachments:
                part2 = MIMEApplication(attachment["binary"])
                part2.add_header("Content-Disposition",
                                 'attachment;filename="%s"' % (attachment["name"]))
                msg.attach(part2)

        return {
            'msg': msg.as_string(),
            'toList': toList,
            'ccList': ccList,
            'bccList': bccList,
            'fromAddr': fromAddr,
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

        to_addrs = msgData['toList'] | msgData['ccList'] | msgData['bccList']
        try:
            Logger.get('mail').info('Sending email: To: {} / CC: {} / BCC: {}'.format(
                ', '.join(msgData['toList']) or 'None',
                ', '.join(msgData['ccList']) or 'None',
                ', '.join(msgData['bccList']) or 'None'))
            server.sendmail(msgData['fromAddr'], to_addrs, msgData['msg'])
        except smtplib.SMTPRecipientsRefused as e:
            raise MaKaCError('Email address is not valid: {}'.format(e.recipients))
        finally:
            server.quit()
        Logger.get('mail').info('Mail sent to {}'.format(', '.join(to_addrs)))

    @classmethod
    @unify_event_args
    def sendAndLog(cls, notification, event, module=None, user=None, skipQueue=False):
        from indico.modules.events.logs import EventLogRealm, EventLogKind
        if isinstance(notification, dict):
            # Wrap a raw dictionary in a notification class
            from indico.legacy.webinterface.mail import GenericNotification
            notification = GenericNotification(notification)
        cls.send(notification, skipQueue=skipQueue)
        log_data = {
            u'content_type': to_unicode(notification.getContentType()),
            u'from': to_unicode(notification.getFromAddr()),
            u'to': map(to_unicode, notification.getToList()),
            u'cc': map(to_unicode, notification.getCCList()),
            u'bcc': map(to_unicode, notification.getBCCList()),
            u'subject': to_unicode(notification.getSubject()).strip(),
            u'body': to_unicode(notification.getBody()).strip()
        }
        summary = u'Sent email: {}'.format(log_data[u'subject'])
        event.log(EventLogRealm.emails, EventLogKind.other, to_unicode(module or u'Unknown'), summary, user,
                  type_=u'email', data=log_data)
