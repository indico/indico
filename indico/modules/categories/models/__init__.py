# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

import textwrap

from sqlalchemy import DDL

from indico.core import signals


@signals.db_schema_created.connect_via('categories')
def _create_check_category_chain_consistency(sender, connection, **kwargs):
    sql = textwrap.dedent("""
        CREATE FUNCTION categories.check_category_chain_consistency() RETURNS trigger AS
        $BODY$
        BEGIN
            IF NOT categories.do_check_category_chain_consistency(NEW.id) THEN
                RAISE EXCEPTION SQLSTATE 'INDX2' USING
                    MESSAGE = 'Categories inconsistent',
                    DETAIL = 'Invalid category chain';
            END IF;

            RETURN NULL;
        END;
        $BODY$
        LANGUAGE plpgsql
    """)
    DDL(sql).execute(connection)


@signals.db_schema_created.connect_via('categories')
def _create_sync_event_category_chains(sender, connection, **kwargs):
    sql = textwrap.dedent("""
        CREATE FUNCTION categories.sync_event_category_chains(cat_id int) RETURNS void AS
        $BODY$
        DECLARE
            rows int;
        BEGIN
            -- use dynamic sql to prevent pg from preparing the statement with a crappy query plan
            EXECUTE $$
                WITH RECURSIVE chains(id, path) AS (
                    SELECT id, ARRAY[id]
                    FROM categories.categories
                    WHERE parent_id IS NULL

                    UNION ALL

                    SELECT cat.id, chains.path || cat.id
                    FROM categories.categories cat, chains
                    WHERE cat.parent_id = chains.id
                )
                UPDATE events.events e
                SET category_chain = chains.path
                FROM chains
                WHERE (e.category_id = $1 OR chains.path @> ARRAY [$1]) AND
                      chains.id = e.category_id AND
                      e.category_chain != chains.path;
            $$ USING cat_id;
            GET DIAGNOSTICS rows = ROW_COUNT;
            RAISE NOTICE 'Synchronized %% rows', rows;
        END;
        $BODY$
        LANGUAGE plpgsql
    """)
    DDL(sql).execute(connection)


@signals.db_schema_created.connect_via('categories')
def _create_do_check_category_chain_consistency(sender, connection, **kwargs):
    sql = textwrap.dedent("""
        CREATE FUNCTION categories.do_check_category_chain_consistency(cat_id int) RETURNS boolean AS
        $BODY$
        DECLARE
            rows int;
            result boolean;
            chain_cte text;
        BEGIN
            CREATE TEMP TABLE IF NOT EXISTS _categories_chain_consistency_cache (
                category_id int,
                cached_result boolean
            ) ON COMMIT DROP;
            SELECT cached_result INTO result FROM _categories_chain_consistency_cache WHERE category_id = cat_id;
            IF FOUND THEN
                RETURN result;
            END IF;

            chain_cte := $$
                WITH RECURSIVE chains(id, path) AS (
                    SELECT id, ARRAY[id]
                    FROM categories.categories
                    WHERE parent_id IS NULL

                    UNION ALL

                    SELECT cat.id, chains.path || cat.id
                    FROM categories.categories cat, chains
                    WHERE cat.parent_id = chains.id
                )
            $$;

            -- use dynamic sql to prevent pg from preparing the statement with a crappy query plan
            EXECUTE $$
                CREATE TEMP TABLE _check_category_chain_consistency_cat_events ON COMMIT DROP AS (
                    $$ || chain_cte || $$
                    SELECT e.id, e.category_id, e.category_chain
                    FROM chains
                    JOIN events.events e ON (e.category_id = chains.id)
                    WHERE chains.path @> ARRAY[$1]
                );
            $$ USING cat_id;

            EXECUTE chain_cte || $$
                SELECT 1
                FROM _check_category_chain_consistency_cat_events e
                JOIN chains ON (chains.id = e.category_id)
                WHERE e.category_chain != chains.path;
            $$;
            GET DIAGNOSTICS rows = ROW_COUNT;
            result := (rows = 0);
            DROP TABLE _check_category_chain_consistency_cat_events;
            INSERT INTO _categories_chain_consistency_cache VALUES (cat_id, result);
            -- If the category is consistent so are all child categories
            IF result THEN
                EXECUTE chain_cte || $$
                    INSERT INTO _categories_chain_consistency_cache
                    SELECT id, $1 FROM chains WHERE id != $2 AND path @> ARRAY[$2]
                $$ USING result, cat_id;
            END IF;
            RETURN result;
        END;
        $BODY$
        LANGUAGE plpgsql
    """)
    DDL(sql).execute(connection)


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
                SELECT id
                FROM events.events
                WHERE NOT is_deleted AND
                      category_chain && (SELECT array_agg(id) FROM categories.categories WHERE is_deleted);
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
