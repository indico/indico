# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from datetime import timedelta
from operator import itemgetter

from indico.core.celery import celery
from indico.core.celery.views import WPCelery
from indico.core.config import config
from indico.modules.admin import RHAdminBase


class RHCeleryTasks(RHAdminBase):
    def _process(self):
        notset = object()
        tasks = []
        for entry in celery.conf['beat_schedule'].values():
            override = config.SCHEDULED_TASK_OVERRIDE.get(entry['task'], notset)
            custom_schedule = None
            disabled = False
            if override is notset:
                pass
            elif not override:
                disabled = True
            elif isinstance(override, dict):
                custom_schedule = override.get('schedule')
            else:
                custom_schedule = override

            tasks.append({'name': entry['task'],
                          'schedule': entry['schedule'],
                          'custom_schedule': custom_schedule,
                          'disabled': disabled})
        tasks.sort(key=itemgetter('disabled', 'name'))

        return WPCelery.render_template('celery_tasks.html', 'celery', tasks=tasks, timedelta=timedelta)
