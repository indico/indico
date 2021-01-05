# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

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
