"""Add index on user merged_into_id

Revision ID: d89585afaf2e
Revises: 26806768cd3f
Create Date: 2021-05-07 18:12:36.384287
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'd89585afaf2e'
down_revision = '26806768cd3f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(None, 'users', ['merged_into_id'], unique=False, schema='users')


def downgrade():
    op.drop_index('ix_users_merged_into_id', table_name='users', schema='users')
