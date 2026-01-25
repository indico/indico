"""Add favorite contributions table

Revision ID: e1e229910f7e
Revises: 932389d22b1f
Create Date: 2026-01-08 16:51:44.198924
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'e1e229910f7e'
down_revision = '932389d22b1f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'favorite_contributions',
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('target_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['target_id'], ['events.contributions.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('user_id', 'target_id'),
        schema='users',
    )


def downgrade():
    op.drop_table('favorite_contributions', schema='users')
