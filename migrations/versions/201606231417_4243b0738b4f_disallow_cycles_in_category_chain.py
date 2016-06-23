"""Disallow cycles in category chain

Revision ID: 4243b0738b4f
Revises: 81e04fbff5
Create Date: 2016-06-23 14:17:08.091420
"""

import textwrap

from alembic import op


# revision identifiers, used by Alembic.
revision = '4243b0738b4f'
down_revision = '81e04fbff5'


def upgrade():
    op.execute(textwrap.dedent('''
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
    '''))
    op.execute('''
        CREATE CONSTRAINT TRIGGER no_cycles
        AFTER INSERT OR UPDATE OF parent_id
        ON categories.categories
        NOT DEFERRABLE
        FOR EACH ROW
        EXECUTE PROCEDURE categories.check_cycles()
    ''')


def downgrade():
    op.execute('DROP TRIGGER no_cycles ON categories.categories')
    op.execute('DROP FUNCTION categories.check_cycles()')
