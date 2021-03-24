# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import logging
import logging.config
import logging.handlers
import os
import warnings
from pprint import pformat

import yaml
from flask import has_request_context, request, session

from indico.core.config import config
from indico.web.util import get_request_info, get_request_user


class AddRequestIDFilter:
    def filter(self, record):
        # Add our request ID if available
        record.request_id = request.id if has_request_context() else '0' * 16
        return True


class AddUserIDFilter:
    def filter(self, record):
        user = get_request_user()[0] if has_request_context() else None
        record.user_id = str(session.user.id) if user else '-'
        return True


class RequestInfoFormatter(logging.Formatter):
    def format(self, record):
        rv = super().format(record)
        info = get_request_info()
        if info:
            rv += '\n\n' + pformat(info)
        return rv


class FormattedSubjectSMTPHandler(logging.handlers.SMTPHandler):
    def getSubject(self, record):
        return self.subject % record.__dict__


class BlacklistFilter(logging.Filter):
    def __init__(self, names):
        self.filters = [logging.Filter(name) for name in names]

    def filter(self, record):
        return not any(x.filter(record) for x in self.filters)


class Logger:
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
        data.setdefault('filters', {})
        data['filters']['_add_request_id'] = {'()': AddRequestIDFilter}
        data['filters']['_add_user_id'] = {'()': AddUserIDFilter}
        for handler in data['handlers'].values():
            handler.setdefault('filters', [])
            handler['filters'].insert(0, '_add_request_id')
            handler['filters'].insert(1, '_add_user_id')
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
                handler.setdefault('fromaddr', f'logger@{config.WORKER_NAME}')
                handler.setdefault('toaddrs', [config.SUPPORT_EMAIL])
                subject = ('Unexpected Exception occurred at {}: %(message)s'
                           if handler['class'] == 'indico.core.logger.FormattedSubjectSMTPHandler' else
                           'Unexpected Exception occurred at {}')
                handler.setdefault('subject', subject.format(config.WORKER_NAME))
        for formatter in data['formatters'].values():
            # Make adding request info to log entries less ugly
            if formatter.pop('append_request_info', False):
                assert '()' not in formatter
                formatter['()'] = RequestInfoFormatter
        # Enable the database logger for our db_log util
        if config.DB_LOG:
            data['loggers']['indico._db'] = {'level': 'DEBUG', 'propagate': False, 'handlers': ['_db']}
            data['handlers']['_db'] = {'class': 'logging.handlers.SocketHandler', 'host': '127.0.0.1', 'port': 9020}
        # If customization debugging is enabled, ensure we get the debug log messages from it
        if config.CUSTOMIZATION_DEBUG and config.CUSTOMIZATION_DIR:
            data['loggers'].setdefault('indico.customization', {})['level'] = 'DEBUG'
        logging.config.dictConfig(data)

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
