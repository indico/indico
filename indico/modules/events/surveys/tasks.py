# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from celery.schedules import crontab

from indico.core.celery import celery
from indico.core.db import db
from indico.modules.events.surveys.models.surveys import Survey


@celery.periodic_task(name='survey_start_notifications', run_every=crontab(minute='*/30'))
def send_start_notifications():
    active_surveys = Survey.find_all(Survey.is_active, ~Survey.start_notification_sent, Survey.notifications_enabled)
    for survey in active_surveys:
        survey.send_start_notification()
    db.session.commit()
