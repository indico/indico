"""Add category consistency functions

Revision ID: 3f25f66e8d5c
Revises: 535f817f2533
Create Date: 2016-06-20 15:28:43.977274
"""

import textwrap

from alembic import op


# revision identifiers, used by Alembic.
revision = '3f25f66e8d5c'
down_revision = '535f817f2533'


def upgrade():
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
    '''))
    op.execute('''
        CREATE CONSTRAINT TRIGGER consistent_deleted
        AFTER INSERT OR UPDATE OF parent_id, is_deleted
        ON categories.categories
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE categories.check_consistency_deleted()
    ''')
    op.execute('''
        CREATE CONSTRAINT TRIGGER consistent_deleted
        AFTER INSERT OR UPDATE OF category_id, is_deleted
        ON events.events
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE categories.check_consistency_deleted()
    ''')


def downgrade():
    op.execute('DROP TRIGGER consistent_deleted ON categories.categories')
    op.execute('DROP TRIGGER consistent_deleted ON events.events')
    op.execute('DROP FUNCTION categories.check_consistency_deleted()')
