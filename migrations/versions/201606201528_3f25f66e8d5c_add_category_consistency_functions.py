"""Add category consistency functions

Revision ID: 3f25f66e8d5c
Revises: 3bdd6bf0181a
Create Date: 2016-06-20 15:28:43.977274
"""

import textwrap

from alembic import op


# revision identifiers, used by Alembic.
revision = '3f25f66e8d5c'
down_revision = '3bdd6bf0181a'


def upgrade():
    op.execute(textwrap.dedent('''
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
    '''))
    op.execute(textwrap.dedent('''
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
    '''))
    op.execute(textwrap.dedent('''
        CREATE FUNCTION events.check_category_chain_consistency() RETURNS trigger AS
        $BODY$
        BEGIN
            IF NOT categories.do_check_category_chain_consistency(NEW.category_id) THEN
                RAISE EXCEPTION SQLSTATE 'INDX2' USING
                MESSAGE = 'Categories inconsistent',
                DETAIL = 'Invalid category chain';
            END IF;

            RETURN NULL;
        END;
        $BODY$
        LANGUAGE plpgsql
    '''))
    op.execute(textwrap.dedent('''
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
    '''))
    op.execute(textwrap.dedent('''
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
            RAISE NOTICE 'Synchronized % rows', rows;
        END;
        $BODY$
        LANGUAGE plpgsql
    '''))
    # deletion consistency
    op.execute('''
        CREATE CONSTRAINT TRIGGER consistent_deleted_insert
        AFTER INSERT
        ON categories.categories
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE categories.check_consistency_deleted()
    ''')
    op.execute('''
        CREATE CONSTRAINT TRIGGER consistent_deleted_update
        AFTER UPDATE OF parent_id, is_deleted
        ON categories.categories
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE categories.check_consistency_deleted()
    ''')
    op.execute('''
        CREATE CONSTRAINT TRIGGER consistent_deleted_insert
        AFTER INSERT
        ON events.events
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE categories.check_consistency_deleted()
    ''')
    op.execute('''
        CREATE CONSTRAINT TRIGGER consistent_deleted_update
        AFTER UPDATE OF category_id, category_chain, is_deleted
        ON events.events
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE categories.check_consistency_deleted()
    ''')
    # chain consistency - from event changes
    op.execute('''
        CREATE CONSTRAINT TRIGGER consistent_category_chain_insert
        AFTER INSERT
        ON events.events
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE events.check_category_chain_consistency()
    ''')
    op.execute('''
        CREATE CONSTRAINT TRIGGER consistent_category_chain_update
        AFTER UPDATE OF category_id, category_chain
        ON events.events
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE events.check_category_chain_consistency()
    ''')
    # chain consistency - from category changes
    op.execute('''
        CREATE CONSTRAINT TRIGGER consistent_category_chain_update
        AFTER UPDATE OF parent_id
        ON categories.categories
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE categories.check_category_chain_consistency();
    ''')


def downgrade():
    op.execute('DROP TRIGGER consistent_category_chain_update ON categories.categories')
    op.execute('DROP TRIGGER consistent_category_chain_insert ON events.events')
    op.execute('DROP TRIGGER consistent_category_chain_update ON events.events')
    op.execute('DROP TRIGGER consistent_deleted_insert ON categories.categories')
    op.execute('DROP TRIGGER consistent_deleted_update ON categories.categories')
    op.execute('DROP TRIGGER consistent_deleted_insert ON events.events')
    op.execute('DROP TRIGGER consistent_deleted_update ON events.events')
    op.execute('DROP FUNCTION events.check_category_chain_consistency()')
    op.execute('DROP FUNCTION categories.check_category_chain_consistency()')
    op.execute('DROP FUNCTION categories.check_consistency_deleted()')
    op.execute('DROP FUNCTION categories.do_check_category_chain_consistency(cat_id integer)')
    op.execute('DROP FUNCTION categories.sync_event_category_chains(cat_id integer)')
