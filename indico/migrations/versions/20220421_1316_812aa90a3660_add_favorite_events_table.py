"""Add favorite events table

Revision ID: 812aa90a3660
Revises: a707753d16e2
Create Date: 2022-04-21 13:16:04.987091
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '812aa90a3660'
down_revision = 'a707753d16e2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'favorite_events',
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('target_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['target_id'], ['events.events.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('user_id', 'target_id'),
        schema='users'
    )


def downgrade():
    op.drop_table('favorite_events', schema='users')
