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

from __future__ import absolute_import, unicode_literals

import cPickle
import os
import tempfile
from datetime import date

from celery.exceptions import MaxRetriesExceededError, Retry
from sqlalchemy.orm.attributes import flag_modified

from indico.core.celery import celery
from indico.core.config import config
from indico.core.db import db
from indico.core.logger import Logger
from indico.util.date_time import now_utc
from indico.util.emails.backend import EmailBackend
from indico.util.emails.message import EmailMessage
from indico.util.string import truncate


logger = Logger.get('emails')
MAX_TRIES = 10
DELAYS = [30, 60, 120, 300, 600, 1800, 3600, 3600, 7200]


@celery.task(name='send_email', bind=True, max_retries=None)
def send_email_task(task, email, log_entry=None):
    attempt = task.request.retries + 1
    try:
        do_send_email(email, log_entry, _from_task=True)
    except Exception as exc:
        delay = (DELAYS + [0])[task.request.retries] if not config.DEBUG else 1
        try:
            task.retry(countdown=delay, max_retries=(MAX_TRIES - 1))
        except MaxRetriesExceededError:
            if log_entry:
                _update_email_log_state(log_entry, failed=True)
                db.session.commit()
            # store the email in case the mail server is  unavailable for an
            # extended period so someone can recover it using `indico shell`
            # and possibly retry sending it
            path = store_failed_email(email)
            logger.error('Could not send email "%s" (attempt %d/%d); giving up [%s]; stored data in %s',
                         truncate(email['subject'], 50), attempt, MAX_TRIES, exc, path)
        except Retry:
            logger.warning('Could not send email "%s" (attempt %d/%d); retry in %ds [%s]',
                           truncate(email['subject'], 50), attempt, MAX_TRIES, delay, exc)
            raise
    else:
        if task.request.retries:
            logger.info('Sent email "%s" (attempt %d/%d)', truncate(email['subject'], 50), attempt, MAX_TRIES)
        else:
            logger.info('Sent email "%s"', truncate(email['subject'], 50))
        # commit the log entry state change
        if log_entry:
            db.session.commit()


def do_send_email(email, log_entry=None, _from_task=False):
    """Send an email"""
    with EmailBackend(timeout=config.SMTP_TIMEOUT) as conn:
        msg = EmailMessage(subject=email['subject'], body=email['body'], from_email=email['from'],
                           to=email['to'], cc=email['cc'], bcc=email['bcc'], reply_to=email['reply_to'],
                           attachments=email['attachments'], connection=conn)
        if email['html']:
            msg.content_subtype = 'html'
        msg.send()
    if not _from_task:
        logger.info('Sent email "%s"', truncate(email['subject'], 50))
    if log_entry:
        _update_email_log_state(log_entry)


def _update_email_log_state(log_entry, failed=False):
    if failed:
        log_entry.data['state'] = 'failed'
    else:
        log_entry.data['state'] = 'sent'
        log_entry.data['sent_dt'] = now_utc(False).isoformat()
    flag_modified(log_entry, 'data')


def store_failed_email(email):
    prefix = 'failed-email-{}-'.format(date.today().isoformat())
    fd, name = tempfile.mkstemp(prefix=prefix, dir=config.TEMP_DIR)
    with os.fdopen(fd, 'wb') as f:
        cPickle.dump(email, f)
    return name
