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

import logging
import os
from operator import itemgetter

from celery import Celery
from celery.app.log import Logging
from celery.beat import PersistentScheduler
from celery.signals import before_task_publish
from contextlib2 import ExitStack
from flask_pluginengine import current_plugin, plugin_context
from sqlalchemy import inspect
from terminaltables import AsciiTable

from indico.core.celery.util import locked_task
from indico.core.config import Config
from indico.core.db import db
from indico.core.plugins import plugin_engine
from indico.util.console import cformat
from indico.util.fossilize import clearCache
from indico.util.string import return_ascii
from indico.web.flask.stats import request_stats_request_started


class IndicoCelery(Celery):
    """Celery sweetened with some Indico/Flask-related sugar

    The following extra params are available on the `task` decorator:

    - `request_context` -- if True, the task will run inside a Flask
                           `test_request_context`
    - `plugin` -- if set to a plugin name or class, the task will run
                  inside a plugin context for that plugin.  This will
                  override whatever plugin context is active when
                  sending the task.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('log', IndicoCeleryLogging)
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
        # Pickle isn't pretty but that way we can pass along all types (tz-aware datetimes, sets, etc.)
        self.conf['CELERY_RESULT_SERIALIZER'] = 'pickle'
        self.conf['CELERY_TASK_SERIALIZER'] = 'pickle'
        self.conf['CELERY_ACCEPT_CONTENT'] = ['json', 'yaml', 'pickle']
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
        assert self.flask_app is None or self.flask_app is app
        self.flask_app = app

    def periodic_task(self, *args, **kwargs):
        """Decorator to register a periodic task.

        This behaves like the :meth:`task` decorator, but automatically
        schedules the task to execute periodically, using extra kwargs
        as described in the Celery documentation:
        http://celery.readthedocs.org/en/latest/userguide/periodic-tasks.html#available-fields

        :param locked: Set this to ``False`` if you want to allow the
                       task to run more than once at the same time.
        """
        def decorator(f):
            if kwargs.pop('locked', True):
                f = locked_task(f)
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
                stack = ExitStack()
                stack.enter_context(self.flask_app.app_context())
                if getattr(s, 'request_context', False):
                    stack.enter_context(self.flask_app.test_request_context(base_url=Config.getInstance().getBaseURL()))
                args = _CelerySAWrapper.unwrap_args(args)
                kwargs = _CelerySAWrapper.unwrap_kwargs(kwargs)
                plugin = getattr(s, 'plugin', kwargs.pop('__current_plugin__', None))
                if isinstance(plugin, basestring):
                    plugin_name = plugin
                    plugin = plugin_engine.get_plugin(plugin)
                    if plugin is None:
                        stack.close()
                        raise ValueError('Plugin not active: ' + plugin_name)
                stack.enter_context(plugin_context(plugin))
                clearCache()
                with stack:
                    request_stats_request_started()
                    return super(IndicoTask, s).__call__(*args, **kwargs)

        self.Task = IndicoTask


class IndicoCeleryLogging(Logging):
    def _configure_logger(self, logger, *args, **kwargs):
        # don't let celery mess with the root logger
        if logger is logging.getLogger():
            return
        super(IndicoCeleryLogging, self)._configure_logger(logger, *args, **kwargs)


class IndicoPersistentScheduler(PersistentScheduler):
    """Celery scheduler that allows indico.conf to override specific entries"""

    def setup_schedule(self):
        deleted = set()
        for task_name, entry in Config.getInstance().getScheduledTaskOverride().iteritems():
            if task_name not in self.app.conf['CELERYBEAT_SCHEDULE']:
                self.logger.error('Invalid entry in ScheduledTaskOverride: %s', task_name)
                continue
            if not entry:
                deleted.add(task_name)
                del self.app.conf['CELERYBEAT_SCHEDULE'][task_name]
            elif isinstance(entry, dict):
                assert entry.get('task') in {None, task_name}  # make sure the task name is not changed
                self.app.conf['CELERYBEAT_SCHEDULE'][task_name].update(entry)
            else:
                self.app.conf['CELERYBEAT_SCHEDULE'][task_name]['schedule'] = entry
        super(IndicoPersistentScheduler, self).setup_schedule()
        self._print_schedule(deleted)

    def _print_schedule(self, deleted):
        table_data = [['Name', 'Schedule']]
        for entry in sorted(self.app.conf['CELERYBEAT_SCHEDULE'].itervalues(), key=itemgetter('task')):
            table_data.append([cformat('%{yellow!}{}%{reset}').format(entry['task']),
                               cformat('%{green}{!r}%{reset}').format(entry['schedule'])])
        for task_name in sorted(deleted):
            table_data.append([cformat('%{yellow}{}%{reset}').format(task_name),
                               cformat('%{red!}Disabled%{reset}')])
        print AsciiTable(table_data, cformat('%{white!}Periodic Tasks%{reset}')).table


class _CelerySAWrapper(object):
    """Wrapper to safely pass SQLAlchemy objects to tasks.

    This is achieved by passing only the model name and its PK values
    through the Celery serializer and then fetching the actual objects
    again when executing the task.
    """
    __slots__ = ('identity_key',)

    def __init__(self, obj):
        self.identity_key = inspect(obj).identity_key
        if self.identity_key is None:
            raise ValueError('Cannot pass non-persistent object to Celery. Did you forget to flush?')

    @property
    def object(self):
        obj = self.identity_key[0].get(self.identity_key[1])
        if obj is None:
            raise ValueError('Object not in DB: {}'.format(self))
        return obj

    @return_ascii
    def __repr__(self):
        model, args = self.identity_key
        return '<{}: {}>'.format(model.__name__, ','.join(map(repr, args)))

    @classmethod
    def wrap_args(cls, args):
        return tuple(cls(x) if isinstance(x, db.Model) else x for x in args)

    @classmethod
    def wrap_kwargs(cls, kwargs):
        return {k: cls(v) if isinstance(v, db.Model) else v for k, v in kwargs.iteritems()}

    @classmethod
    def unwrap_args(cls, args):
        return tuple(x.object if isinstance(x, cls) else x for x in args)

    @classmethod
    def unwrap_kwargs(cls, kwargs):
        return {k: v.object if isinstance(v, cls) else v for k, v in kwargs.iteritems()}


@before_task_publish.connect
def before_task_publish_signal(*args, **kwargs):
    body = kwargs['body']
    body['args'] = _CelerySAWrapper.wrap_args(body['args'])
    body['kwargs'] = _CelerySAWrapper.wrap_kwargs(body['kwargs'])
    if current_plugin:
        body['kwargs']['__current_plugin__'] = current_plugin.name
