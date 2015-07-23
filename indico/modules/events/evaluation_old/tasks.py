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

from __future__ import unicode_literals

from celery.schedules import crontab

from indico.core.celery import celery
from indico.core.db import db
from indico.core.notifications import make_email, send_email
from indico.modules.events.evaluation_old import event_settings as evaluation_settings
from indico.util.date_time import now_utc
from indico.web.flask.templating import get_template_module
from MaKaC.evaluation import Evaluation


@celery.periodic_task(name='evaluation_old_start_notifications', run_every=crontab(minute='0', hour='0'))
def notify_evaluation_start():
    for setting in evaluation_settings.query.filter_by(name='send_notification'):
        if not setting.value:
            continue
        event = setting.event
        if _process_evaluation(event):
            evaluation_settings.delete(event, 'send_notification')
            db.session.commit()


def _process_evaluation(event):
    """Processes the notification for a single evaluation

    :return: ``True`` if the event shouldn't be checked for evaluation
             notifications again because the notification has been sent
             or shouldn't be sent at all.
    """

    evaluation = event.getEvaluation()
    now = now_utc()
    if not evaluation.isVisible():
        # Evaluation disabled? We shouldn't be here. Simply don't
        # do anything and disable the send_notification flag.
        return True
    elif now >= evaluation.getEndDate():
        # Evaluation finished. Doesn't make lots of sense either
        # but in that case we also don't want to spam people.
        return True
    elif not evaluation.getNbOfQuestions():
        # Evaluation is empty.
        return True
    elif now < evaluation.getStartDate():
        # Evaluation not started yet. Don't do anything in this
        # case but keep checking the event.
        return False

    notification = evaluation.getNotification(Evaluation._EVALUATION_START)
    if not notification or (not notification.getToList() and not notification.getCCList()):
        # Notifications disabled
        return True

    tpl = get_template_module('events/evaluation_old/emails/evaluation_started.txt', event=event, evaluation=evaluation)
    # XXX: This is terrible, putting possibly all the participants in `To`. We should really use BCC for this!
    email = make_email(notification.getToList(), notification.getCCList(), template=tpl)
    send_email(email, event, 'Evaluation')
    return True
