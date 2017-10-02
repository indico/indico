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
import logging.config
import logging.handlers
import os
import warnings
from pprint import pformat

import yaml
from flask import current_app, has_request_context, request, session

from indico.core.config import config
from indico.util.i18n import set_best_lang
from indico.web.util import get_request_info


try:
    from raven.contrib.celery import register_logger_signal, register_signal, CeleryFilter
    from raven.contrib.flask import Sentry
    from raven.handlers.logging import SentryHandler
except ImportError:
    Sentry = object  # so we can subclass
    has_sentry = False
else:
    has_sentry = True


class AddRequestIDFilter(object):
    def filter(self, record):
        # Add our request ID if available
        record.request_id = request.id if has_request_context() else '0' * 12
        return True


class RequestInfoFormatter(logging.Formatter):
    def format(self, record):
        rv = super(RequestInfoFormatter, self).format(record)
        return rv + '\n\n' + pformat(get_request_info())


class FormattedSubjectSMTPHandler(logging.handlers.SMTPHandler):
    def getSubject(self, record):
        return self.subject % record.__dict__


class Logger(object):
    @classmethod
    def init(cls, app):
        path = config.LOGGING_CONFIG_PATH
        if not path:
            return
        if not os.path.exists(path):
            default_path = os.path.join(app.root_path, 'logging.yaml.sample')
            warnings.warn('Logging config file not found; using defaults. '
                          'Copy {default_path} to {path} to get rid of this warning.'
                          .format(path=path, default_path=default_path))
            path = default_path
        with open(path) as f:
            data = yaml.safe_load(f)
        data['disable_existing_loggers'] = False
        data['incremental'] = False
        # Make the request ID available in all loggers
        data.setdefault('filters', {})['_add_request_id'] = {'()': AddRequestIDFilter}
        for handler in data['handlers'].itervalues():
            handler.setdefault('filters', []).append('_add_request_id')
            if handler['class'] == 'logging.FileHandler' and handler['filename'][0] != '/':
                # Make relative paths relative to the log dir
                handler['filename'] = os.path.join(config.LOG_DIR, handler['filename'])
            elif handler['class'] in ('logging.handlers.SMTPHandler', 'indico.core.logger.FormattedSubjectSMTPHandler'):
                # Configure email handlers with the data from the config
                if not handler.get('mailhost'):
                    handler['mailhost'] = config.SMTP_SERVER
                    handler['secure'] = () if config.SMTP_USE_TLS else None  # yuck, empty tuple == STARTTLS
                    if config.SMTP_LOGIN and config.SMTP_PASSWORD:
                        handler['credentials'] = (config.SMTP_LOGIN, config.SMTP_PASSWORD)
                handler.setdefault('fromaddr', 'logger@{}'.format(config.WORKER_NAME))
                handler.setdefault('toaddrs', [config.SUPPORT_EMAIL])
                subject = ('Unexpected Exception occurred at {}: %(message)s'
                           if handler['class'] == 'indico.core.logger.FormattedSubjectSMTPHandler' else
                           'Unexpected Exception occurred at {}')
                handler.setdefault('subject', subject.format(config.WORKER_NAME))
        for formatter in data['formatters'].itervalues():
            # Make adding request info to log entries less ugly
            if formatter.pop('append_request_info', False):
                assert '()' not in formatter
                formatter['()'] = RequestInfoFormatter
        # Enable the database logger for our db_log util
        if config.DB_LOG:
            data['loggers']['indico._db'] = {'level': 'DEBUG', 'propagate': False, 'handlers': ['_db']}
            data['handlers']['_db'] = {'class': 'logging.handlers.SocketHandler', 'host': '127.0.0.1', 'port': 9020}
        logging.config.dictConfig(data)
        if config.SENTRY_DSN:
            if not has_sentry:
                raise Exception('`raven` must be installed to use sentry logging')
            init_sentry(app)

    @classmethod
    def get(cls, name=None):
        """Get a logger with the given name.

        This behaves pretty much like `logging.getLogger`, except for
        prefixing any logger name with ``indico.`` (if not already
        present).
        """
        if name is None:
            name = 'indico'
        elif name != 'indico' and not name.startswith('indico.'):
            name = 'indico.' + name
        return logging.getLogger(name)


class IndicoSentry(Sentry):
    def get_user_info(self, request):
        if not has_request_context() or not session.user:
            return None
        return {'id': session.user.id,
                'email': session.user.email,
                'name': session.user.full_name}

    def before_request(self, *args, **kwargs):
        super(IndicoSentry, self).before_request()
        if not has_request_context():
            return
        self.client.extra_context({'Endpoint': str(request.url_rule.endpoint) if request.url_rule else None})
        self.client.tags_context({'locale': set_best_lang()})


class RHFilter(logging.Filter):
    def filter(self, record):
        # we don't want to send RH log messages (especially exceptions)
        # to sentry since they are already logged as exceptions
        return record.name != 'indico.rh'


def init_sentry(app):
    sentry = IndicoSentry(dsn=config.SENTRY_DSN, logging=True, level=getattr(logging, config.SENTRY_LOGGING_LEVEL))
    sentry.init_app(app)
    # connect to the indico logger (sentry only registers itself on the
    # root logger, and the indico logger does not propagate its messages)
    handler = SentryHandler(sentry.client, level=sentry.level)
    handler.addFilter(RHFilter())
    Logger.get().addHandler(handler)
    # connect to the celery logger
    register_signal(sentry.client)
    handler = SentryHandler(sentry.client, level=sentry.level)
    handler.addFilter(CeleryFilter())
    logging.getLogger('celery').addHandler(handler)


def sentry_log_exception():
    try:
        sentry = current_app.extensions['sentry']
    except KeyError:
        return
    sentry.captureException()


def sentry_set_extra(data):
    """
    Set extra data to be logged in sentry if the current request
    results in something to be sent to sentry.

    :param data: A dict containing data.
    """
    try:
        sentry = current_app.extensions['sentry']
    except KeyError:
        return
    sentry.client.extra_context(data)


def sentry_set_tags(data):
    """
    Set extra tag data to be logged in sentry if the current request
    results in something to be sent to sentry.

    :param data: A dict containing tag data.
    """
    try:
        sentry = current_app.extensions['sentry']
    except KeyError:
        return
    sentry.client.tags_context(data)
