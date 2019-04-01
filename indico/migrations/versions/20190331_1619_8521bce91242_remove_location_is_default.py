"""Remove location is_default

Revision ID: 8521bce91242
Revises: fe73a07da0b4
Create Date: 2019-03-31 16:19:23.467808
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '8521bce91242'
down_revision = 'fe73a07da0b4'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('locations', 'is_default', schema='roombooking')


def downgrade():
    op.add_column('locations', sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
                  schema='roombooking')
    op.alter_column('locations', 'is_default', server_default=None, schema='roombooking')
    op.execute('''
        WITH cte AS (
            SELECT id FROM roombooking.locations ORDER BY id ASC LIMIT 1
        )
        UPDATE roombooking.locations loc
        SET is_default = true
        FROM cte
        WHERE loc.id = cte.id
    ''')
