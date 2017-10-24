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

from celery.exceptions import MaxRetriesExceededError, Retry
from sqlalchemy.orm.attributes import flag_modified

from indico.core.celery import celery
from indico.core.config import config
from indico.core.db import db
from indico.core.logger import Logger
from indico.util.date_time import now_utc
from indico.util.emails.message import EmailMessage
from indico.util.string import truncate


logger = Logger.get('emails')
MAX_TRIES = 10
DELAYS = [30, 60, 120, 300, 600, 1800, 3600, 3600, 7200]


@celery.task(name='send_email', bind=True, max_retries=None)
def send_email_task(task, email, log_entry=None):
    try:
        do_send_email(email, log_entry)
    except Exception as exc:
        attempt = task.request.retries + 1
        delay = (DELAYS + [0])[task.request.retries] if not config.DEBUG else 1
        try:
            task.retry(countdown=delay, max_retries=(MAX_TRIES - 1))
        except MaxRetriesExceededError:
            if log_entry:
                _update_email_log_state(log_entry, failed=True)
                db.session.commit()
            logger.error('Could not send email "%s" (attempt %d/%d); giving up [%s]',
                         truncate(email['subject'], 50), attempt, MAX_TRIES, exc)
        except Retry:
            logger.warning('Could not send email "%s" (attempt %d/%d); retry in %ds [%s]',
                           truncate(email['subject'], 50), attempt, MAX_TRIES, delay, exc)
            raise
    else:
        # commit the log entry state change
        if log_entry:
            db.session.commit()


def do_send_email(email, log_entry=None):
    """Send an email"""
    attachments = [(a['name'], a['binary']) for a in email['attachments']]
    msg = EmailMessage(subject=email['subject'], body=email['body'], from_email=email['from'],
                       to=email['to'], cc=email['cc'], bcc=email['bcc'], reply_to=email['reply_to'],
                       attachments=attachments)
    if email['html']:
        msg.content_subtype = 'html'
    msg.send()
    # TODO: log errors
    if log_entry:
        _update_email_log_state(log_entry)


def _update_email_log_state(log_entry, failed=False):
    if failed:
        log_entry.data['state'] = 'failed'
    else:
        log_entry.data['state'] = 'sent'
        log_entry.data['sent_dt'] = now_utc(False).isoformat()
    flag_modified(log_entry, 'data')
