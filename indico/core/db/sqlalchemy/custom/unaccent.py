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

from sqlalchemy import DDL, text
from flask import current_app

from indico.core.db.sqlalchemy.util.queries import has_extension


# if you wonder why search_path is set and the two-argument `unaccent` function is used,
# see this post on stackoverflow: http://stackoverflow.com/a/11007216/298479
SQL_FUNCTION_UNACCENT = '''
    CREATE FUNCTION indico_unaccent(value TEXT)
        RETURNS TEXT
    AS $$
    BEGIN
        RETURN unaccent('unaccent', value);
    END;
    $$
    LANGUAGE plpgsql IMMUTABLE SET search_path = public, pg_temp;
'''

SQL_FUNCTION_NOOP = '''
    CREATE FUNCTION indico_unaccent(value TEXT)
        RETURNS TEXT
    AS $$
    BEGIN
        RETURN value;
    END;
    $$
    LANGUAGE plpgsql IMMUTABLE;
'''


def _should_create_function(ddl, target, connection, **kw):
    sql = "SELECT COUNT(*) FROM information_schema.routines WHERE routine_name = 'indico_unaccent'"
    count = connection.execute(text(sql)).scalar()
    return not count


def create_unaccent_function(conn):
    """Creates the unaccent function if it doesn't exist yet.

    In TESTING mode it always uses the no-op version to have a
    consistent database setup.
    """
    if not current_app.config['TESTING'] and has_extension(conn, 'unaccent'):
        DDL(SQL_FUNCTION_UNACCENT).execute_if(callable_=_should_create_function).execute(conn)
    else:
        if not current_app.config['TESTING']:
            print 'Warning: unaccent extension is not available'
        DDL(SQL_FUNCTION_NOOP).execute_if(callable_=_should_create_function).execute(conn)
