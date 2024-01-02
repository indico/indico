# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
import pickle
import tempfile
from datetime import date
from email.headerregistry import parser
from email.utils import make_msgid
from fnmatch import fnmatch
from urllib.parse import urlsplit

import click
from celery.exceptions import MaxRetriesExceededError, Retry
from sqlalchemy.orm.attributes import flag_modified

from indico.core.celery import celery
from indico.core.config import config
from indico.core.db import db
from indico.core.logger import Logger
from indico.util.date_time import now_utc
from indico.util.string import truncate
from indico.vendor.django_mail import get_connection
from indico.vendor.django_mail.message import EmailMessage


logger = Logger.get('emails')
MAX_TRIES = 10
DELAYS = [30, 60, 120, 300, 600, 1800, 3600, 3600, 7200]


@celery.task(name='send_email', bind=True, max_retries=None)
def send_email_task(task, email, log_entry=None):
    attempt = task.request.retries + 1
    try:
        do_send_email(email, log_entry, _from_task=True)
    except Exception as exc:
        delay = ([*DELAYS, 0])[task.request.retries] if not config.DEBUG else 1
        try:
            task.retry(countdown=delay, max_retries=(MAX_TRIES - 1))
        except MaxRetriesExceededError:
            if log_entry:
                update_email_log_state(log_entry, failed=True)
                db.session.commit()
            # store the email in case the mail server is  unavailable for an
            # extended period so someone can recover it using `indico shell`
            # and possibly retry sending it
            path = store_failed_email(email, log_entry)
            logger.error('Could not send email "%s" (attempt %d/%d); giving up [%s]; stored data in %s',
                         truncate(email['subject'], 100), attempt, MAX_TRIES, exc, path)
        except Retry:
            logger.warning('Could not send email "%s" (attempt %d/%d); retry in %ds [%s]',
                           truncate(email['subject'], 100), attempt, MAX_TRIES, delay, exc)
            raise
    else:
        if task.request.retries:
            logger.info('Sent email "%s" (attempt %d/%d)', truncate(email['subject'], 100), attempt, MAX_TRIES)
        else:
            logger.info('Sent email "%s"', truncate(email['subject'], 100))
        # commit the log entry state change
        if log_entry:
            db.session.commit()


def _rewrite_sender(msg: EmailMessage):
    if not config.SMTP_SENDER_FALLBACK:
        # no fallback set, cannot rewrite. let's hope all emails go through...
        return

    from_email_raw = parser.get_mailbox(msg.from_email)[0].addr_spec  # just the addr without a name part
    if not any(fnmatch(from_email_raw, pattern) for pattern in config.SMTP_ALLOWED_SENDERS):
        msg.extra_headers['From'] = msg.from_email
        msg.from_email = config.SMTP_SENDER_FALLBACK


def do_send_email(email, log_entry=None, _from_task=False):
    """Send an email.

    This function should not be called directly unless your
    goal is to send an email *right now* without nice error
    handling or retrying.  For pretty much all cases where
    you just want to send an email, use `send_email` instead.

    :param email: The data describign the email, as created by
                  `make_email`
    :param log_entry: An `EventLogEntry` for the email in case it was
                      sent in the context of an event.  After sending
                      the email, the log entry's state will be updated
                      to indicate that the email has been sent.
    :param _from_task: Indicates that this function is called from
                       the celery task responsible for sending emails.
    """
    with get_connection() as conn:
        msg = EmailMessage(subject=email['subject'], body=email['body'], from_email=email['from'],
                           to=email['to'], cc=email['cc'], bcc=email['bcc'], reply_to=email['reply_to'],
                           attachments=email['attachments'], connection=conn)
        if not msg.to:
            msg.extra_headers['To'] = 'Undisclosed-recipients:;'
        _rewrite_sender(msg)
        if email['html']:
            msg.content_subtype = 'html'
        msg.extra_headers['message-id'] = make_msgid(domain=urlsplit(config.BASE_URL).hostname)
        msg.send()
    if not _from_task:
        logger.info('Sent email "%s"', truncate(email['subject'], 100))
    if log_entry:
        update_email_log_state(log_entry)


def update_email_log_state(log_entry, failed=False):
    if failed:
        log_entry.data['state'] = 'failed'
    else:
        log_entry.data['state'] = 'sent'
        log_entry.data['sent_dt'] = now_utc(False).isoformat()
    flag_modified(log_entry, 'data')


def store_failed_email(email, log_entry=None):
    prefix = f'failed-email-{date.today().isoformat()}-'
    fd, name = tempfile.mkstemp(prefix=prefix, dir=config.TEMP_DIR)
    with os.fdopen(fd, 'wb') as f:
        pickle.dump((email, log_entry.id if log_entry else None), f)
    return name


def resend_failed_email(path):
    """Try re-sending an email that previously failed."""
    from indico.modules.logs import EventLogEntry
    with open(path, 'rb') as f:
        email, log_entry_id = pickle.load(f)  # noqa: S301
    log_entry = EventLogEntry.get(log_entry_id) if log_entry_id is not None else None
    do_send_email(email, log_entry)
    db.session.commit()
    os.remove(path)
    return email


def resend_failed_emails_cmd(paths):
    for path in paths:
        email = resend_failed_email(path)
        click.secho('Email sent: "{}" ({})'.format(truncate(email['subject'], 100), os.path.basename(path)), fg='green')
