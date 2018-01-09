# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals

import re
import time
from functools import wraps
from types import GeneratorType

from flask import g

from indico.core.config import config
from indico.core.db import db
from indico.core.logger import Logger
from indico.util.string import to_unicode, truncate


logger = Logger.get('emails')


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


def send_email(email, event=None, module=None, user=None):
    """Sends an email created by :func:`make_email`.

    When called while inside a RH, the email will be queued and only
    sent or passed on to celery once the database commit succeeded.

    :param email: The email object returned by :func:`make_email`
    :param event: If specified, the email will be saved in that
                  event's log
    :param module: The module name to show in the email log
    :param user: The user to show in the email log
    """
    from indico.core.emails import do_send_email, send_email_task
    fn = send_email_task.delay if config.SMTP_USE_CELERY else do_send_email
    # we log the email immediately (as pending).  if we don't commit,
    # the log message will simply be thrown away later
    log_entry = _log_email(email, event, module, user)
    if 'email_queue' in g:
        g.email_queue.append((fn, email, log_entry))
    else:
        fn(email, log_entry)


def _log_email(email, event, module, user):
    from indico.modules.events.logs import EventLogKind, EventLogRealm
    if not event:
        return None
    log_data = {
        'content_type': 'text/html' if email['html'] else 'text/plain',
        'from': email['from'],
        'to': sorted(email['to']),
        'cc': sorted(email['cc']),
        'bcc': sorted(email['bcc']),
        'subject': email['subject'],
        'body': email['body'].strip(),
        'state': 'pending',
        'sent_dt': None,
    }
    return event.log(EventLogRealm.emails, EventLogKind.other, to_unicode(module or 'Unknown'), log_data['subject'],
                     user, type_='email', data=log_data)


def init_email_queue():
    """Enable email queueing for the current context."""
    g.setdefault('email_queue', [])


def flush_email_queue():
    """Send all the emails in the queue.

    Note: This function does a database commit to update states
    in case of failures or immediately-sent emails.  It should only
    be called if the session is in a state safe to commit or after
    doing a commit/rollback of any other changes that might have
    been pending.
    """
    from indico.core.emails import store_failed_email, update_email_log_state
    queue = g.get('email_queue', [])
    if not queue:
        return
    logger.debug('Sending %d queued emails', len(queue))
    for fn, email, log_entry in queue:
        try:
            fn(email, log_entry)
        except Exception:
            # Flushing the email queue happens after a commit.
            # If anything goes wrong here we keep going and just log
            # it to avoid losing (more) emails in case celery is not
            # used for email sending or there is a temporary issue
            # with celery.
            if log_entry:
                update_email_log_state(log_entry, failed=True)
            path = store_failed_email(email, log_entry)
            logger.exception('Flushing queued email "%s" failed; stored data in %s',
                             truncate(email['subject'], 100), path)
            # Wait for a short moment in case it's a very temporary issue
            time.sleep(0.25)
    del queue[:]
    db.session.commit()


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
    :param reply_address: The reply-to address or a collection of addresses.
                          Defaults to empty.
    :param attachments: A list of attachments. Each attachment can be
                        a `MIMEBase` subclass, a 3-tuple of the form
                        ``(filename, content, mimetype)``, or a 2-tuple
                        ``(filename, content)`` in which case the mime
                        type will be guessed from the file name.
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
    if config.DEBUG and '\n' in subject:
        raise ValueError('Email subject contains linebreaks')
    subject = re.sub(r'\s+', ' ', subject)
    if to_list is None:
        to_list = set()
    if cc_list is None:
        cc_list = set()
    if bcc_list is None:
        bcc_list = set()
    to_list = {to_list} if isinstance(to_list, basestring) else to_list
    cc_list = {cc_list} if isinstance(cc_list, basestring) else cc_list
    bcc_list = {bcc_list} if isinstance(bcc_list, basestring) else bcc_list
    reply_address = {reply_address} if isinstance(reply_address, basestring) else (reply_address or set())
    return {
        'to': set(map(to_unicode, to_list)),
        'cc': set(map(to_unicode, cc_list)),
        'bcc': set(map(to_unicode, bcc_list)),
        'from': to_unicode(from_address or config.NO_REPLY_EMAIL),
        'reply_to': set(map(to_unicode, reply_address)),
        'attachments': attachments or [],
        'subject': to_unicode(subject).strip(),
        'body': to_unicode(body).strip(),
        'html': html,
    }
