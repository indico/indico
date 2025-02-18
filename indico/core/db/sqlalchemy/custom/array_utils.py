# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
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

SQL_FUNCTION_TEXT_ARRAY_APPEND = '''
    CREATE FUNCTION indico.text_array_append(arr text[], item text)
        RETURNS text[]
    AS $$
    BEGIN
        RETURN array_append(arr, item);
    END;
    $$
    LANGUAGE plpgsql IMMUTABLE STRICT;
'''

SQL_FUNCTION_TEXT_ARRAY_TO_STRING = '''
    CREATE FUNCTION indico.text_array_to_string(arr text[], sep text)
        RETURNS text
    AS $$
    BEGIN
        RETURN array_to_string(arr, sep);
    END;
    $$
    LANGUAGE plpgsql IMMUTABLE STRICT;
'''


def _make_exec_if(func_name):
    def _should_create_function(ddl, target, connection, **kw):
        sql = f'''
            SELECT COUNT(*)
            FROM information_schema.routines
            WHERE routine_schema = 'indico' AND routine_name = '{func_name}'
        '''  # noqa: S608
        count = connection.execute(text(sql)).scalar()
        return not count

    return _should_create_function


def create_array_is_unique_function(conn):
    DDL(SQL_FUNCTION_ARRAY_IS_UNIQUE).execute_if(callable_=_make_exec_if('array_is_unique')).execute(conn)


def create_array_append_function(conn):
    DDL(SQL_FUNCTION_TEXT_ARRAY_APPEND).execute_if(callable_=_make_exec_if('text_array_append')).execute(conn)


def create_array_to_string_function(conn):
    DDL(SQL_FUNCTION_TEXT_ARRAY_TO_STRING).execute_if(callable_=_make_exec_if('text_array_to_string')).execute(conn)
