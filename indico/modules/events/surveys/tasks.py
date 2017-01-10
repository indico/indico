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

from __future__ import unicode_literals

from celery.schedules import crontab

from indico.core.celery import celery
from indico.core.db import db
from indico.modules.events.surveys.models.surveys import Survey


@celery.periodic_task(name='survey_start_notifications', run_every=crontab(minute='*/30'))
def send_start_notifications():
    active_surveys = Survey.find_all(Survey.is_active, ~Survey.start_notification_sent, Survey.notifications_enabled)
    try:
        for survey in active_surveys:
            survey.send_start_notification()
    finally:
        db.session.commit()
