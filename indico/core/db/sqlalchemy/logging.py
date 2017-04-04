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

from __future__ import absolute_import

import logging
import pprint
import time
import traceback

from flask import (current_app, g, appcontext_tearing_down, request_tearing_down, request_started, request,
                   has_request_context)
from sqlalchemy.engine import Engine
from sqlalchemy.event import listens_for

from indico.core.db import db
from indico.core.plugins import plugin_engine
from indico.web.flask.stats import get_request_stats


def _prettify_sql(statement):
    return '    ' + statement.replace('\n', '\n    ')


def _prettify_params(args):
    return '    ' + pprint.pformat(args).replace('\n', '\n    ')


def _interesting_tb_item(item, paths):
    return (item[0].endswith('.tpl.py') or any(item[0].startswith(p) for p in paths)) and 'sqlalchemy' not in item[0]


def _get_sql_line():
    paths = [current_app.root_path] + [p.root_path for p in plugin_engine.get_active_plugins().itervalues()]
    stack = [item for item in reversed(traceback.extract_stack()) if _interesting_tb_item(item, paths)]
    for i, item in enumerate(stack):
        return {'file': item[0],
                'line': item[1],
                'function': item[2],
                'items': stack[i:i+5]}


def _fix_param(param):
    if hasattr(param, 'iteritems'):
        return {k: _fix_param(v) for k, v in param.iteritems()}
    return '<binary>' if param.__class__.__name__ == 'Binary' else param


def apply_db_loggers(app):
    if not app.debug or getattr(db, '_loggers_applied', False):
        return
    db._loggers_applied = True
    from indico.core.logger import Logger

    logger = Logger.get('db')
    logger.setLevel(logging.DEBUG)

    @listens_for(Engine, 'before_cursor_execute')
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        if not g.get('req_start_sent'):
            g.req_start_sent = True
            logger.debug('Request started', extra={'sql_log_type': 'start_request',
                                                   'repl': app.config.get('REPL'),
                                                   'req_verb': request.method if has_request_context() else None,
                                                   'req_path': request.path if has_request_context() else None,
                                                   'req_url': request.url if has_request_context() else None})

        context._query_start_time = time.time()
        source_line = _get_sql_line()
        if source_line:
            log_msg = 'Start Query:\n    {0[file]}:{0[line]} {0[function]}\n\n{1}\n{2}'.format(
                source_line,
                _prettify_sql(statement),
                _prettify_params(parameters) if parameters else ''
            ).rstrip()
        else:
            # UPDATEs can't be traced back to their source since they are executed only on flush
            log_msg = 'Start Query:\n{0}\n{1}'.format(
                _prettify_sql(statement),
                _prettify_params(parameters) if parameters else ''
            ).rstrip()
        # psycopg2._psycopg.Binary objects are extremely weird and don't work in isinstance checks
        if hasattr(parameters, 'iteritems'):
            parameters = {k: _fix_param(v) for k, v in parameters.iteritems()}
        else:
            parameters = tuple(_fix_param(v) for v in parameters)
        logger.debug(log_msg,
                     extra={'sql_log_type': 'start',
                            'req_path': request.path if has_request_context() else None,
                            'sql_source': source_line['items'] if source_line else None,
                            'sql_statement': statement,
                            'sql_verb': statement.split()[0],
                            'sql_params': parameters})

    @listens_for(Engine, 'after_cursor_execute')
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total = time.time() - context._query_start_time
        source_line = _get_sql_line()
        source = source_line['items'] if source_line else None
        logger.debug('Query complete; total time: %s', total, extra={'sql_log_type': 'end',
                                                                     'req_path': (request.path
                                                                                  if has_request_context()
                                                                                  else None),
                                                                     'sql_source': source,
                                                                     'sql_duration': total,
                                                                     'sql_verb': statement.split()[0]})

    @appcontext_tearing_down.connect_via(app)
    @request_tearing_down.connect_via(app)
    def on_tearing_down(sender, **kwargs):
        if g.get('req_end_sent'):
            return
        g.req_end_sent = True
        stats = get_request_stats()
        if not stats['query_count']:
            return
        logger.debug('Request finished', extra={'sql_log_type': 'end_request',
                                                'sql_query_count': stats['query_count'],
                                                'repl': app.config.get('REPL'),
                                                'req_verb': request.method if has_request_context() else None,
                                                'req_url': request.url if has_request_context() else None,
                                                'req_path': request.path if has_request_context() else None,
                                                'req_duration': stats['req_duration'],
                                                'req_query_duration': stats['query_duration']})
