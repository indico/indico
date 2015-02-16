# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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
from MaKaC.common.mail import GenericMailer
from MaKaC.webinterface.mail import GenericNotification


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
            GenericMailer.send(GenericNotification(mail))
    return wrapper


def make_email(to_list, cc_list=None, from_address=None, attachments=None,
               subject=None, body=None, template=None, html=False):
    if template is not None and (subject is not None or body is not None):
        raise ValueError("Only subject/body or template can be passed")
    if template:
        subject = template.get_subject()
        body = template.get_body()
    if cc_list is None:
        cc_list = []
    to_list = [to_list] if isinstance(to_list, basestring) else to_list
    cc_list = [cc_list] if isinstance(cc_list, basestring) else cc_list
    if not from_address:
        from_address = Config.getInstance().getNoReplyEmail()
    return {
        'toList': to_list,
        'ccList': cc_list,
        'fromAddr': from_address,
        'attachments': attachments,
        'subject': subject,
        'body': body,
        'content-type': 'text/html' if html else 'text/plain'
    }
