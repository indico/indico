"""Add code to affiliations

Revision ID: e5a08c20f2bc
Revises: 577e564cf0ae
Create Date: 2026-03-23 17:28:10.101572
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'e5a08c20f2bc'
down_revision = '577e564cf0ae'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('affiliations', sa.Column('code', sa.String(), nullable=False, server_default=''), schema='indico')
    op.alter_column('affiliations', 'code', server_default=None, schema='indico')
    op.drop_index('ix_affiliations_searchable_names_unaccent', table_name='affiliations', schema='indico')
    op.drop_index('ix_affiliations_searchable_names_fts', table_name='affiliations', schema='indico')
    op.execute('''
        CREATE INDEX ix_affiliations_searchable_names_unaccent
        ON indico.affiliations
        USING gin (indico.indico_unaccent(lower(indico.text_array_to_string(((ARRAY[''::text] || indico.text_array_append(indico.text_array_append((alt_names)::text[], (name)::text), (code)::text)) || ARRAY[''::text]), '|||'::text))) gin_trgm_ops);
    ''')
    op.execute('''
        CREATE INDEX ix_affiliations_searchable_names_fts
        ON indico.affiliations
        USING gin (to_tsvector('simple'::regconfig, indico.text_array_to_string(((ARRAY[''::text] || indico.text_array_append(indico.text_array_append((alt_names)::text[], (name)::text), (code)::text)) || ARRAY[''::text]), '|||'::text)));
    ''')


def downgrade():
    op.drop_index('ix_affiliations_searchable_names_unaccent', table_name='affiliations', schema='indico')
    op.drop_index('ix_affiliations_searchable_names_fts', table_name='affiliations', schema='indico')
    op.drop_column('affiliations', 'code', schema='indico')
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
