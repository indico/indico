# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy import DDL, text


SQL_FUNCTION_ARRAY_IS_UNIQUE = '''
    CREATE FUNCTION indico.array_is_unique(value text[])
        RETURNS boolean
    AS $$
        SELECT COALESCE(COUNT(DISTINCT a) = array_length(value, 1), true)
        FROM unnest(value) a
    $$
    LANGUAGE SQL IMMUTABLE STRICT;
'''


def _should_create_function(ddl, target, connection, **kw):
    sql = '''
        SELECT COUNT(*)
        FROM information_schema.routines
        WHERE routine_schema = 'indico' AND routine_name = 'array_is_unique'
    '''
    count = connection.execute(text(sql)).scalar()
    return not count


def create_array_is_unique_function(conn):
    DDL(SQL_FUNCTION_ARRAY_IS_UNIQUE).execute_if(callable_=_should_create_function).execute(conn)
