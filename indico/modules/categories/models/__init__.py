# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import textwrap

from sqlalchemy import DDL

from indico.core import signals


@signals.db_schema_created.connect_via('categories')
def _create_check_consistency_deleted(sender, connection, **kwargs):
    sql = textwrap.dedent("""
        CREATE FUNCTION categories.check_consistency_deleted() RETURNS trigger AS
        $BODY$
        DECLARE
            rows int;
        BEGIN
            CREATE TEMP TABLE IF NOT EXISTS _categories_consistency_deleted_checked (dummy bool) ON COMMIT DROP;
            IF EXISTS (SELECT 1 FROM _categories_consistency_deleted_checked) THEN
                RETURN NULL;
            ELSE
                INSERT INTO _categories_consistency_deleted_checked VALUES (true);
            END IF;
            -- use dynamic sql to prevent pg from preparing the statement with a crappy query plan
            EXECUTE $$
                WITH RECURSIVE chains(id, path, is_deleted) AS (
                    SELECT id, ARRAY[id], is_deleted
                    FROM categories.categories
                    WHERE parent_id IS NULL

                    UNION ALL

                    SELECT cat.id, chains.path || cat.id, chains.is_deleted OR cat.is_deleted
                    FROM categories.categories cat, chains
                    WHERE cat.parent_id = chains.id
                )
                SELECT 1
                FROM events.events e
                JOIN chains ON (chains.id = e.category_id)
                WHERE NOT e.is_deleted AND chains.is_deleted;
            $$;
            GET DIAGNOSTICS rows = ROW_COUNT;
            IF rows != 0 THEN
                RAISE EXCEPTION SQLSTATE 'INDX1' USING
                    MESSAGE = 'Categories inconsistent',
                    DETAIL = 'Event inside deleted category';
            END IF;

            EXECUTE $$
                SELECT 1
                FROM categories.categories cat
                JOIN categories.categories parent ON (parent.id = cat.parent_id)
                WHERE NOT cat.is_deleted AND parent.is_deleted;
            $$;
            GET DIAGNOSTICS rows = ROW_COUNT;
            IF rows != 0 THEN
                RAISE EXCEPTION SQLSTATE 'INDX1' USING
                    MESSAGE = 'Categories inconsistent',
                    DETAIL = 'Subcategory inside deleted category';
            END IF;
            RETURN NULL;
        END;
        $BODY$
        LANGUAGE plpgsql
    """)
    DDL(sql).execute(connection)


@signals.db_schema_created.connect_via('categories')
def _create_check_cycles(sender, connection, **kwargs):
    sql = textwrap.dedent("""
        CREATE FUNCTION categories.check_cycles() RETURNS trigger AS
        $BODY$
        DECLARE
            rows int;
        BEGIN
            -- use dynamic sql to prevent pg from preparing the statement with a crappy query plan
            EXECUTE $$
                WITH RECURSIVE chains(id, path, is_cycle) AS (
                    SELECT id, ARRAY[id], false
                    FROM categories.categories

                    UNION ALL

                    SELECT cat.id, chains.path || cat.id, cat.id = ANY(chains.path)
                    FROM categories.categories cat, chains
                    WHERE cat.parent_id = chains.id AND NOT chains.is_cycle
                )
                SELECT 1 FROM chains WHERE is_cycle;
            $$;
            GET DIAGNOSTICS rows = ROW_COUNT;
            IF rows != 0 THEN
                RAISE EXCEPTION SQLSTATE 'INDX2' USING
                    MESSAGE = 'Categories inconsistent',
                    DETAIL = 'Cycle detected';
            END IF;

            RETURN NULL;
        END;
        $BODY$
        LANGUAGE plpgsql
    """)
    DDL(sql).execute(connection)
