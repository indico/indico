"""Add Location.is_deleted

Revision ID: a83e77e11e36
Revises: ad0625914645
Create Date: 2019-04-23 14:31:00.215481
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'a83e77e11e36'
down_revision = 'ad0625914645'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('locations', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
                  schema='roombooking')
    op.alter_column('locations', 'is_deleted', server_default=None, schema='roombooking')
    op.drop_index('ix_uq_locations_name', table_name='locations', schema='roombooking')
    op.create_index(None, 'locations', ['name'], unique=True, postgresql_where=sa.text('NOT is_deleted'),
                    schema='roombooking')


def downgrade():
    op.drop_index('ix_uq_locations_name', table_name='locations', schema='roombooking')
    op.drop_column('locations', 'is_deleted', schema='roombooking')
    op.create_index(None, 'locations', ['name'], unique=True, schema='roombooking')
