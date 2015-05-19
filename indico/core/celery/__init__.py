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

from indico.core.config import Config
from indico.core.db import DBMgr


celery = Celery('indico')
celery.flask_app = None  # set from configure_celery


class IndicoTask(celery.Task):
    """Celery task which runs inside the indico environment"""
    abstract = True

    def __call__(self, *args, **kwargs):
        with celery.flask_app.app_context():
            with DBMgr.getInstance().global_connection():
                return super(IndicoTask, self).__call__(*args, **kwargs)


celery.Task = IndicoTask


def configure_celery(app):
    cfg = Config.getInstance()
    broker_url = cfg.getCeleryBroker()
    if not broker_url and not app.config['TESTING']:
        raise ValueError('Celery broker URL is not set')
    celery.conf['BROKER_URL'] = broker_url
    celery.conf['CELERY_RESULT_BACKEND'] = cfg.getCeleryResultBackend() or broker_url
    celery.conf['CELERYBEAT_SCHEDULER'] = IndicoPersistentScheduler
    celery.conf['CELERYBEAT_SCHEDULE_FILENAME'] = os.path.join(cfg.getTempDir(), 'celerybeat-schedule')
    celery.conf['CELERYD_HIJACK_ROOT_LOGGER'] = False
    celery.conf['CELERY_TIMEZONE'] = cfg.getDefaultTimezone()
    celery.conf['CELERY_STORE_ERRORS_EVEN_IF_IGNORED'] = True
    celery.conf['CELERY_REDIRECT_STDOUTS'] = not app.debug
    # Pickle isn't pretty but that way we can pass along all types (tz-aware datetimes, sets, etc.)
    celery.conf['CELERY_RESULT_SERIALIZER'] = 'pickle'
    celery.conf['CELERY_TASK_SERIALIZER'] = 'pickle'
    celery.conf['CELERY_ACCEPT_CONTENT'] = ['pickle']
    # Send emails about failed tasks
    celery.conf['CELERY_SEND_TASK_ERROR_EMAILS'] = True
    celery.conf['ADMINS'] = [('Admin', cfg.getSupportEmail())]
    celery.conf['SERVER_EMAIL'] = 'Celery <{}>'.format(cfg.getNoReplyEmail())
    celery.conf['EMAIL_HOST'] = cfg.getSmtpServer()[0]
    celery.conf['EMAIL_PORT'] = cfg.getSmtpServer()[1]
    celery.conf['EMAIL_USE_TLS'] = cfg.getSmtpUseTLS()
    celery.conf['EMAIL_HOST_USER'] = cfg.getSmtpLogin() or None
    celery.conf['EMAIL_HOST_PASWORD'] = cfg.getSmtpPassword() or None
    # Allow indico.conf to override settings
    celery.conf.update(cfg.getCeleryConfig())
    assert celery.flask_app is None
    celery.flask_app = app


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
