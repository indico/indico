"""Add alternate names to affiliations

Revision ID: c7d6c3641918
Revises: b212f6d17229
Create Date: 2025-02-14 11:36:35.560567
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'c7d6c3641918'
down_revision = 'b212f6d17229'
branch_labels = None
depends_on = None


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


def upgrade():
    op.execute(SQL_FUNCTION_TEXT_ARRAY_APPEND)
    op.execute(SQL_FUNCTION_TEXT_ARRAY_TO_STRING)
    op.add_column('affiliations', sa.Column('alt_names', postgresql.ARRAY(sa.String()),
                                            nullable=False, server_default='{}'), schema='indico')
    op.alter_column('affiliations', 'alt_names', server_default=None, schema='indico')
    op.execute('''
        CREATE INDEX ix_affiliations_searchable_names_unaccent
        ON indico.affiliations
        USING gin (indico.indico_unaccent(lower(indico.text_array_to_string(((ARRAY[''::text] || indico.text_array_append((alt_names)::text[], (name)::text)) || ARRAY[''::text]), '|||'::text))) gin_trgm_ops);
    ''')
    op.execute('''
        CREATE INDEX ix_affiliations_searchable_names_fts
        ON indico.affiliations
        USING gin (to_tsvector('simple'::regconfig, indico.text_array_to_string(((ARRAY[''::text] || indico.text_array_append((alt_names)::text[], (name)::text)) || ARRAY[''::text]), '|||'::text)));
    ''')


def downgrade():
    op.drop_index('ix_affiliations_searchable_names_unaccent', table_name='affiliations', schema='indico')
    op.drop_column('affiliations', 'alt_names', schema='indico')
    op.execute('DROP FUNCTION indico.text_array_append(arr text[], item text)')
    op.execute('DROP FUNCTION indico.text_array_to_string(arr text[], sep text)')
