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

from functools import wraps
from types import GeneratorType

from indico.core.config import Config
from indico.legacy.common.mail import GenericMailer


def email_sender(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        mails = fn(*args, **kwargs)
        if mails is None:
            return
        if isinstance(mails, GeneratorType):
            mails = list(mails)
        elif not isinstance(mails, list):
            mails = [mails]
        for mail in filter(None, mails):
            send_email(mail)
    return wrapper


def send_email(email, event=None, module='', user=None, skip_queue=False):
    """Sends an email created by :func:`make_email`.

    :param email: The email object returned by :func:`make_email`
    :param event: If specified, the email will be saved in that
                  event's log
    :param module: The module name to show in the email log
    :param user: The user to show in the email log
    :param skip_queue: If true, the email will be sent immediately
                       instead of being queued until after commit even
                       while inside a RH context
    """
    if event is not None:
        GenericMailer.sendAndLog(email, event, module=module, user=user, skipQueue=skip_queue)
    else:
        GenericMailer.send(email, skipQueue=skip_queue)


def make_email(to_list=None, cc_list=None, bcc_list=None, from_address=None, reply_address=None, attachments=None,
               subject=None, body=None, template=None, html=False):
    """Creates an email.

    The preferred way to specify the email content is using the
    `template` argument. To do so, use :func:`.get_template_module` on
    a template inheriting from ``emails/base.txt`` for test emails or
    ``emails/base.html`` for HTML emails.

    :param to_list: The recipient email or a collection of emails
    :param cc_list: The CC email or a collection of emails
    :param bcc_list: The BCC email or a collection of emails
    :param from_address: The sender address. Defaults to noreply.
    :param reply_address: The reply-to address. Defaults to empty.
    :param attachments: A list of attachments, consisting of dicts
                        containing ``name`` and ``binary`` keys.
    :param subject: The subject of the email.
    :param body: The body of the email:
    :param template: A template module containing ``get_subject`` and
                     ``get_body`` macros.
    :param html: ``True`` if the email body is HTML
    """
    if template is not None and (subject is not None or body is not None):
        raise ValueError("Only subject/body or template can be passed")
    if template:
        subject = template.get_subject()
        body = template.get_body()
    if to_list is None:
        to_list = set()
    if cc_list is None:
        cc_list = set()
    if bcc_list is None:
        bcc_list = set()
    to_list = {to_list} if isinstance(to_list, basestring) else to_list
    cc_list = {cc_list} if isinstance(cc_list, basestring) else cc_list
    bcc_list = {bcc_list} if isinstance(bcc_list, basestring) else bcc_list
    if not from_address:
        from_address = Config.getInstance().getNoReplyEmail()
    return {
        'toList': set(to_list),
        'ccList': set(cc_list),
        'bccList': set(bcc_list),
        'fromAddr': from_address,
        'replyAddr': reply_address,
        'attachments': attachments,
        'subject': subject,
        'body': body,
        'content-type': 'text/html' if html else 'text/plain'
    }
