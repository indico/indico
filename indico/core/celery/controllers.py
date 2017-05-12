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

from datetime import timedelta
from operator import itemgetter

from indico.core.celery.views import WPCelery
from indico.modules.admin import RHAdminBase

from indico.core.celery import celery
from indico.core.config import Config


class RHCeleryTasks(RHAdminBase):
    def _process(self):
        flower_url = Config.getInstance().getFlowerURL()

        notset = object()
        overridden_tasks = Config.getInstance().getScheduledTaskOverride()
        tasks = []
        for entry in celery.conf['CELERYBEAT_SCHEDULE'].values():
            override = overridden_tasks.get(entry['task'], notset)
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

        return WPCelery.render_template('celery_tasks.html', 'celery',
                                        flower_url=flower_url, tasks=tasks, timedelta=timedelta)
