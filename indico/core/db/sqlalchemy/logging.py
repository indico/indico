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

from sqlalchemy.engine import Engine
from sqlalchemy.event import listens_for

# Optional dependencies for pretty SQL logging
try:
    import sqlparse
except ImportError:
    sqlparse = None

try:
    from pygments import highlight
    from pygments.lexers import SqlLexer, PythonLexer
    from pygments.formatters import Terminal256Formatter
except ImportError:
    has_pygments = False
else:
    has_pygments = True


def _prettify_sql(statement):
    if sqlparse:
        statement = sqlparse.format(statement, keyword_case='upper', reindent=True)
    statement = '    ' + statement.replace('\n', '\n    ')
    if not has_pygments or os.environ.get('INDICO_COLORED_LOG') != '1':
        return statement
    return highlight(statement, SqlLexer(), Terminal256Formatter(style='native'))


def _prettify_params(args):
    args = pprint.pformat(args)
    args = '    ' + args.replace('\n', '\n    ')
    if not has_pygments or os.environ.get('INDICO_COLORED_LOG') != '1':
        return args
    return highlight(args, PythonLexer(), Terminal256Formatter(style='native')).rstrip()

def _prettify_traceback(args):
    args = pprint.pformat(args)
    args = args.replace('\n', '')
    if not has_pygments or os.environ.get('INDICO_COLORED_LOG') != '1':
        return args
    return highlight(args, PythonLexer(), Terminal256Formatter(style='native')).strip()


def _get_sql_line():
    import indico

    indico_path = os.path.dirname(os.path.abspath(indico.__file__))
    root_path = "{}/".format(os.path.dirname(indico_path))
    stack = traceback.extract_stack()
    for item in reversed(stack):
        if item[0].startswith(indico_path) and 'logging' not in item[0] and 'sqlalchemy' not in item[0]:
            module_name = os.path.splitext(item[0].replace(root_path, ''))[0].replace(os.sep, '.')
            return '{}:{} {}'.format(_prettify_traceback(module_name),
                                     _prettify_traceback(item[1]),
                                     _prettify_traceback(item[2]))


def apply_db_loggers(debug=False):
    if not debug:
        return
    from indico.core.logger import Logger

    logger = Logger.get('db')
    logger.setLevel(logging.DEBUG)

    @listens_for(Engine, 'before_cursor_execute')
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        context._query_start_time = time.time()
        msg = 'Start Query:\n    {}\n\n{}\n{}'
        logger.debug(msg.format(_get_sql_line(), _prettify_sql(statement),
                                _prettify_params(parameters) if parameters else '').rstrip())

    @listens_for(Engine, 'after_cursor_execute')
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total = time.time() - context._query_start_time
        logger.debug('Query complete; total time: {}'.format(total))
