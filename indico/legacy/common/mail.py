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
from email.utils import formatdate

from indico.core.config import config
from indico.core.logger import Logger
from indico.util.string import to_unicode


# Prevent base64 encoding of utf-8 e-mails
charset.add_charset('utf-8', charset.SHORTEST)


class GenericMailer:
    @staticmethod
    def _prepare(email):
        fromAddr = email['from']
        replyAddr = email['reply_to']
        toList = set(filter(None, email['to']))
        ccList = set(filter(None, email['cc']))
        bccList = set(filter(None, email['bcc']))

        if not toList and not ccList and not bccList:
            return

        msg = MIMEMultipart()
        msg["Subject"] = to_unicode(email['subject']).strip()
        msg["From"] = fromAddr
        msg["To"] = ', '.join(toList) if toList else 'Undisclosed-recipients:;'
        if ccList:
            msg["Cc"] = ', '.join(ccList)
        if replyAddr:
            msg['Reply-to'] = replyAddr
        msg["Date"] = formatdate()

        body = email['body']
        if email['html']:
            part1 = MIMEText(body, "html", "utf-8")
        else:
            part1 = MIMEText(body, "plain", "utf-8")
        msg.attach(part1)

        for attachment in email['attachments']:
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
        server = smtplib.SMTP(*config.SMTP_SERVER)
        if config.SMTP_USE_TLS:
            server.ehlo()
            (code, errormsg) = server.starttls()
            if code != 220:
                raise Exception('Cannot start secure connection to SMTP server: {}, {}'.format(code, errormsg))
        if config.SMTP_LOGIN:
            login = config.SMTP_LOGIN
            password = config.SMTP_PASSWORD
            (code, errormsg) = server.login(login, password)
            if code != 235:
                raise Exception('Cannot login on SMTP server: {}, {}'.format(code, errormsg))

        to_addrs = msgData['toList'] | msgData['ccList'] | msgData['bccList']
        try:
            Logger.get('mail').info(u'Sending email: To: {} / CC: {} / BCC: {}'.format(
                u', '.join(msgData['toList']) or 'None',
                u', '.join(msgData['ccList']) or 'None',
                u', '.join(msgData['bccList']) or 'None'))
            server.sendmail(msgData['fromAddr'], to_addrs, msgData['msg'])
        except smtplib.SMTPRecipientsRefused as e:
            raise ValueError('Email address is not valid: {}'.format(e.recipients))
        finally:
            server.quit()
        Logger.get('mail').info('Mail sent to {}'.format(', '.join(to_addrs)))
