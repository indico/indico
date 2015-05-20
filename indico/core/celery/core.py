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

import os

from celery import Celery
from celery.beat import PersistentScheduler

from indico.core.celery import CELERY_IMPORTS
from indico.core.config import Config
from indico.core.db import DBMgr


class IndicoCelery(Celery):
    """Celery sweetened with some Indico/Flask-related sugar"""

    def __init__(self, *args, **kwargs):
        super(IndicoCelery, self).__init__(*args, **kwargs)
        self.flask_app = None  # set from configure_celery
        self._patch_task()

    def init_app(self, app):
        cfg = Config.getInstance()
        broker_url = cfg.getCeleryBroker()
        if not broker_url and not app.config['TESTING']:
            raise ValueError('Celery broker URL is not set')
        self.conf['BROKER_URL'] = broker_url
        self.conf['CELERY_RESULT_BACKEND'] = cfg.getCeleryResultBackend() or broker_url
        self.conf['CELERYBEAT_SCHEDULER'] = IndicoPersistentScheduler
        self.conf['CELERYBEAT_SCHEDULE_FILENAME'] = os.path.join(cfg.getTempDir(), 'celerybeat-schedule')
        self.conf['CELERYD_HIJACK_ROOT_LOGGER'] = False
        self.conf['CELERY_TIMEZONE'] = cfg.getDefaultTimezone()
        self.conf['CELERY_IGNORE_RESULT'] = True
        self.conf['CELERY_STORE_ERRORS_EVEN_IF_IGNORED'] = True
        self.conf['CELERY_REDIRECT_STDOUTS'] = not app.debug
        self.conf['CELERY_IMPORTS'] = CELERY_IMPORTS
        # Pickle isn't pretty but that way we can pass along all types (tz-aware datetimes, sets, etc.)
        self.conf['CELERY_RESULT_SERIALIZER'] = 'pickle'
        self.conf['CELERY_TASK_SERIALIZER'] = 'pickle'
        self.conf['CELERY_ACCEPT_CONTENT'] = ['pickle']
        # Send emails about failed tasks
        self.conf['CELERY_SEND_TASK_ERROR_EMAILS'] = True
        self.conf['ADMINS'] = [('Admin', cfg.getSupportEmail())]
        self.conf['SERVER_EMAIL'] = 'Celery <{}>'.format(cfg.getNoReplyEmail())
        self.conf['EMAIL_HOST'] = cfg.getSmtpServer()[0]
        self.conf['EMAIL_PORT'] = cfg.getSmtpServer()[1]
        self.conf['EMAIL_USE_TLS'] = cfg.getSmtpUseTLS()
        self.conf['EMAIL_HOST_USER'] = cfg.getSmtpLogin() or None
        self.conf['EMAIL_HOST_PASWORD'] = cfg.getSmtpPassword() or None
        # Allow indico.conf to override settings
        self.conf.update(cfg.getCeleryConfig())
        assert self.flask_app is None
        self.flask_app = app

    def periodic_task(self, *args, **kwargs):
        """Decorator to register a periodic task.

        This behaves like the :meth:`task` decorator, but automatically
        schedules the task to execute periodically, using extra kwargs
        as described in the Celery documentation:
        http://celery.readthedocs.org/en/latest/userguide/periodic-tasks.html#available-fields
        """
        def decorator(f):
            entry = {
                'schedule': kwargs.pop('run_every'),
                'args': kwargs.pop('args', ()),
                'kwargs': kwargs.pop('kwargs', {}),
                'options': kwargs.pop('options', {}),
                'relative': kwargs.pop('relative', False)
            }
            kwargs.setdefault('ignore_result', True)
            task = self.task(f, *args, **kwargs)
            entry['task'] = task.name
            self.conf['CELERYBEAT_SCHEDULE'][task.name] = entry
            return task

        return decorator

    def _patch_task(self):
        """Patches the `task` decorator to run tasks inside the indico environment"""
        class IndicoTask(self.Task):
            abstract = True

            def __call__(s, *args, **kwargs):
                with self.flask_app.app_context():
                    with DBMgr.getInstance().global_connection():
                        return super(IndicoTask, s).__call__(*args, **kwargs)

        self.Task = IndicoTask


class IndicoPersistentScheduler(PersistentScheduler):
    """Celery scheduler that allows indico.conf to override specific entries"""

    def setup_schedule(self):
        for task_name, entry in Config.getInstance().getScheduledTaskOverride().iteritems():
            if task_name not in self.app.conf['CELERYBEAT_SCHEDULE']:
                self.logger.error('Invalid entry in ScheduledTaskOverride: ' + task_name)
                continue
            if not entry:
                del self.app.conf['CELERYBEAT_SCHEDULE'][task_name]
            elif isinstance(entry, dict):
                assert entry.get('task') in {None, task_name}  # make sure the task name is not changed
                self.app.conf['CELERYBEAT_SCHEDULE'][task_name].update(entry)
            else:
                self.app.conf['CELERYBEAT_SCHEDULE'][task_name]['schedule'] = entry
        super(IndicoPersistentScheduler, self).setup_schedule()
