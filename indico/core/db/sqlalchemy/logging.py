# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import

import logging
import os
import pprint
import time
import traceback

from flask import current_app
from sqlalchemy.engine import Engine
from sqlalchemy.event import listens_for


def _prettify_sql(statement):
    return '    ' + statement.replace('\n', '\n    ')


def _prettify_params(args):
    return '    ' + pprint.pformat(args).replace('\n', '\n    ')


def _get_sql_line():
    indico_path = current_app.root_path
    root_path = "{}/".format(os.path.dirname(indico_path))
    stack = list(reversed(traceback.extract_stack()))
    for i, item in enumerate(stack):
        if item[0].startswith(indico_path) and 'logging' not in item[0] and 'sqlalchemy' not in item[0]:
            module_name = os.path.splitext(item[0].replace(root_path, ''))[0].replace(os.sep, '.')
            return {'module': module_name,
                    'line': item[1],
                    'function': item[2],
                    'items': stack[i:i+3]}


def apply_db_loggers(debug=False):
    if not debug:
        return
    from indico.core.logger import Logger

    logger = Logger.get('db')
    logger.setLevel(logging.DEBUG)

    @listens_for(Engine, 'before_cursor_execute')
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        context._query_start_time = time.time()
        source_line = _get_sql_line()
        if source_line:
            log_msg = 'Start Query:\n    {0[module]}:{0[line]} {0[function]}\n\n{1}\n{2}'.format(
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
        logger.debug(log_msg,
                     extra={'sql_log_type': 'start',
                            'sql_source': source_line['items'] if source_line else None,
                            'sql_statement': statement,
                            'sql_params': parameters})

    @listens_for(Engine, 'after_cursor_execute')
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total = time.time() - context._query_start_time
        logger.debug('Query complete; total time: {}'.format(total), extra={'sql_log_type': 'end',
                                                                            'sql_duration': total})
