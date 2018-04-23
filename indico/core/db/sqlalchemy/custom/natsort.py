# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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


SQL_FUNCTION_NATSORT = '''
    CREATE FUNCTION indico.natsort(value TEXT)
        RETURNS bytea
    AS $$
    SELECT string_agg(
        convert_to(coalesce(r[2], length(length(r[1])::text) || length(r[1])::text || r[1]), 'SQL_ASCII'),
        ' '
    )
    FROM regexp_matches(value, '0*([0-9]+)|([^0-9]+)', 'g') r;
    $$
    LANGUAGE SQL IMMUTABLE STRICT;
'''


def _should_create_function(ddl, target, connection, **kw):
    sql = """
        SELECT COUNT(*)
        FROM information_schema.routines
        WHERE routine_schema = 'indico' AND routine_name = 'natsort'
    """
    count = connection.execute(text(sql)).scalar()
    return not count


def create_natsort_function(conn):
    DDL(SQL_FUNCTION_NATSORT).execute_if(callable_=_should_create_function).execute(conn)
