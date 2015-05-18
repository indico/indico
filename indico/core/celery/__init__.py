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

from celery import Celery

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
    broker_url = Config.getInstance().getCeleryBroker()
    if not broker_url:
        raise ValueError('Celery broker URL is not set')
    celery.conf['BROKER_URL'] = broker_url
    celery.conf['CELERY_RESULT_BACKEND'] = Config.getInstance().getCeleryResultBackend() or broker_url
    celery.conf['CELERY_RESULT_SERIALIZER'] = 'yaml'
    celery.conf['CELERY_TASK_SERIALIZER'] = 'yaml'
    celery.conf['CELERY_ACCEPT_CONTENT'] = ['yaml']
    celery.conf['CELERYD_HIJACK_ROOT_LOGGER'] = app.debug  # in debug mode logging on stdout is nicer!
    assert celery.flask_app is None
    celery.flask_app = app

