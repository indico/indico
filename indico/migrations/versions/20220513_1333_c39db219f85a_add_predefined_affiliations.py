"""Add predefined affiliations

Revision ID: c39db219f85a
Revises: 812aa90a3660
Create Date: 2022-04-07 13:33:30.611028
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'c39db219f85a'
down_revision = '812aa90a3660'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'affiliations',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('name', sa.String(), nullable=False, index=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('street', sa.String(), nullable=False),
        sa.Column('postcode', sa.String(), nullable=False),
        sa.Column('city', sa.String(), nullable=False),
        sa.Column('country_code', sa.String(), nullable=False),
        sa.Column('meta', postgresql.JSONB(), nullable=False),
        schema='indico'
    )
    op.create_index(None, 'affiliations', ['meta'], unique=False, schema='indico', postgresql_using='gin')
    op.add_column('affiliations', sa.Column('affiliation_id', sa.Integer(), nullable=True), schema='users')
    op.create_index(None, 'affiliations', ['affiliation_id'], unique=False, schema='users')
    op.create_foreign_key(None, 'affiliations', 'affiliations', ['affiliation_id'], ['id'],
                          source_schema='users', referent_schema='indico')


def downgrade():
    op.drop_column('affiliations', 'affiliation_id', schema='users')
    op.drop_table('affiliations', schema='indico')
